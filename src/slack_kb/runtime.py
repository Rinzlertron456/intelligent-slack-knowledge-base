from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from slack_kb.answer_graph import AnswerGraph
from slack_kb.config import Settings
from slack_kb.database import Database
from slack_kb.database import apply_migrations as apply_database_migrations
from slack_kb.ingestion import IngestionService
from slack_kb.openai_service import OpenAIService
from slack_kb.slack_app import SlackKnowledgeApp


@dataclass
class SlackRuntime:
    database: Database
    handler: SocketModeHandler

    def close(self) -> None:
        self.handler.close()
        self.database.close()


def migration_directory() -> Path:
    return Path(__file__).resolve().parents[2] / "supabase" / "migrations"


def build_slack_runtime(
    settings: Settings,
    *,
    apply_migrations: bool = False,
) -> SlackRuntime:
    settings.validate_slack()
    database_url = settings.database_url.get_secret_value()
    if apply_migrations:
        apply_database_migrations(database_url, migration_directory())

    database = Database(database_url)
    database.open()
    try:
        openai = OpenAIService(settings)
        answer_graph = AnswerGraph(database, openai, settings)
        ingestion = IngestionService(
            database,
            openai,
            org_admin_user_ids=settings.org_admins,
        )
        app = App(token=settings.slack_bot_token.get_secret_value())
        SlackKnowledgeApp(
            app=app,
            database=database,
            openai=openai,
            answer_graph=answer_graph,
            ingestion=ingestion,
        )
        return SlackRuntime(
            database=database,
            handler=SocketModeHandler(
                app,
                settings.slack_app_token.get_secret_value(),
            ),
        )
    except Exception:
        database.close()
        raise
