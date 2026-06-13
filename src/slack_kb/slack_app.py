from __future__ import annotations

import logging
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import httpx
from slack_bolt import App

from slack_kb.answer_graph import AnswerGraph
from slack_kb.commands import ParsedCommand, parse_command
from slack_kb.database import Database
from slack_kb.ingestion import IngestionService
from slack_kb.models import KnowledgeScope, RequestContext
from slack_kb.openai_service import OpenAIService
from slack_kb.parsers import parse_file, parse_plain_text, parse_url
from slack_kb.slack_formatting import HELP_TEXT, format_answer
from slack_kb.slack_threads import is_slack_permalink, load_slack_thread

LOGGER = logging.getLogger(__name__)


class SlackKnowledgeApp:
    def __init__(
        self,
        *,
        app: App,
        database: Database,
        openai: OpenAIService,
        answer_graph: AnswerGraph,
        ingestion: IngestionService,
    ):
        self.app = app
        self.database = database
        self.openai = openai
        self.answer_graph = answer_graph
        self.ingestion = ingestion
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="kb-worker")
        self._register_handlers()

    def _register_handlers(self) -> None:
        @self.app.command("/knowledge")
        def knowledge_command(ack, command, respond, client):
            ack()
            try:
                parsed = parse_command(command.get("text", ""))
            except ValueError as error:
                respond(str(error), response_type="ephemeral")
                return
            context = RequestContext(
                workspace_id=command["team_id"],
                user_id=command["user_id"],
                channel_id=command["channel_id"],
                thread_key=f"slash:{command['channel_id']}:{command['user_id']}",
            )
            respond("Working on it...", response_type="ephemeral")
            self.executor.submit(
                self._run_command,
                parsed,
                context,
                respond,
                client,
                None,
            )

        @self.app.event("app_mention")
        def app_mention(ack, event, client, body):
            ack()
            text = re.sub(r"<@[A-Z0-9]+>", "", event.get("text", ""), count=1).strip()
            try:
                parsed = parse_command(text)
            except ValueError as error:
                client.chat_postMessage(
                    channel=event["channel"],
                    thread_ts=event.get("thread_ts") or event["ts"],
                    text=str(error),
                )
                return
            context = RequestContext(
                workspace_id=body["team_id"],
                user_id=event["user"],
                channel_id=event["channel"],
                thread_key=event.get("thread_ts") or event["ts"],
            )
            client.chat_postMessage(
                channel=event["channel"],
                thread_ts=context.thread_key,
                text="Working on it...",
            )
            self.executor.submit(
                self._run_command,
                parsed,
                context,
                None,
                client,
                event.get("files") or [],
            )

        @self.app.event("message")
        def direct_message(ack, event, client, body):
            ack()
            if (
                event.get("channel_type") != "im"
                or event.get("bot_id")
                or event.get("subtype")
            ):
                return
            try:
                parsed = parse_command(event.get("text", ""))
            except ValueError as error:
                client.chat_postMessage(channel=event["channel"], text=str(error))
                return
            context = RequestContext(
                workspace_id=body["team_id"],
                user_id=event["user"],
                channel_id=event["channel"],
                thread_key=event.get("thread_ts") or event["ts"],
            )
            self.executor.submit(
                self._run_command,
                parsed,
                context,
                None,
                client,
                event.get("files") or [],
            )

    def _run_command(
        self,
        parsed: ParsedCommand,
        context: RequestContext,
        respond,
        client,
        files: list[dict[str, Any]] | None,
    ) -> None:
        try:
            output = self._execute(parsed, context, files or [], client)
        except (PermissionError, ValueError) as error:
            output = str(error)
        except Exception:
            LOGGER.exception("Slack command failed", extra={"action": parsed.action})
            output = "I couldn't complete that request. Check the ingestion status or service logs."

        if respond is not None:
            respond(output, response_type="ephemeral")
        elif client is not None:
            client.chat_postMessage(
                channel=context.channel_id,
                thread_ts=context.thread_key,
                text=output,
                unfurl_links=False,
            )

    def _execute(
        self,
        parsed: ParsedCommand,
        context: RequestContext,
        files: list[dict[str, Any]],
        client,
    ) -> str:
        if parsed.action == "help":
            return HELP_TEXT
        if parsed.action == "ask":
            return format_answer(self.answer_graph.ask(context, parsed.argument))
        if parsed.action == "status":
            documents = self.database.recent_documents(context)
            if not documents:
                return "No accessible documents have been indexed yet."
            lines = [
                f"• `{item['id']}` *{item['title']}* ({item['scope']})"
                for item in documents
            ]
            return "*Recently indexed knowledge*\n" + "\n".join(lines)
        if parsed.action == "summarize":
            document = self.database.get_document_for_user(
                context=context,
                document_id=parsed.argument,
            )
            if not document:
                return "That document does not exist or is outside your current knowledge scope."
            summary = self.openai.summarize(
                title=document["title"],
                content=document["content"],
            )
            source = (
                f"\n\n<{document['source_url']}|Open source>"
                if document.get("source_url")
                else ""
            )
            return f"{summary}{source}"
        if parsed.action == "add":
            scope = parsed.scope or KnowledgeScope.PERSONAL
            document_ids: list[str] = []
            for file_info in files:
                document_ids.append(self._ingest_slack_file(context, scope, file_info))
            if parsed.argument:
                if is_slack_permalink(parsed.argument):
                    if client is None:
                        raise ValueError("Slack thread ingestion requires a Slack client")
                    payload = load_slack_thread(
                        client=client,
                        permalink=parsed.argument,
                        request_channel_id=context.channel_id,
                    )
                elif parsed.argument.startswith(("https://", "http://")):
                    payload = parse_url(parsed.argument)
                else:
                    payload = parse_plain_text(parsed.argument)
                document_ids.append(
                    self.ingestion.ingest(context=context, scope=scope, payload=payload)
                )
            if not document_ids:
                return "Attach a supported file or provide a URL/text after the scope."
            ids = ", ".join(f"`{document_id}`" for document_id in document_ids)
            return f"Indexed {len(document_ids)} item(s) as *{scope.value}* knowledge: {ids}"
        return HELP_TEXT

    def _ingest_slack_file(
        self,
        context: RequestContext,
        scope: KnowledgeScope,
        file_info: dict[str, Any],
    ) -> str:
        download_url = file_info.get("url_private_download") or file_info.get("url_private")
        if not download_url:
            raise ValueError("Slack did not provide a downloadable file URL")
        token = self.app.client.token
        response = httpx.get(
            download_url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
            follow_redirects=True,
        )
        response.raise_for_status()
        permalink = file_info.get("permalink")
        payload = parse_file(
            file_info.get("name") or "slack-file",
            response.content,
            source_url=permalink,
        )
        return self.ingestion.ingest(context=context, scope=scope, payload=payload)
