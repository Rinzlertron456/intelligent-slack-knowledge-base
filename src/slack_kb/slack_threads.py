from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.parse import parse_qs, urlparse

from slack_kb.models import DocumentPayload


@dataclass(frozen=True)
class SlackThreadReference:
    channel_id: str
    thread_ts: str


class SlackRepliesClient(Protocol):
    def conversations_replies(self, **kwargs: Any) -> Any: ...


def is_slack_permalink(value: str) -> bool:
    try:
        host = (urlparse(value).hostname or "").lower()
    except ValueError:
        return False
    return host == "slack.com" or host.endswith(".slack.com")


def parse_slack_permalink(url: str) -> SlackThreadReference:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if host != "slack.com" and not host.endswith(".slack.com"):
        raise ValueError("The URL is not a Slack message permalink")

    match = re.search(r"/archives/([A-Z0-9]+)/p(\d{11,})", parsed.path)
    if not match:
        raise ValueError("The Slack permalink does not contain a channel and message ID")
    channel_id, compact_ts = match.groups()
    if len(compact_ts) < 7:
        raise ValueError("The Slack permalink timestamp is invalid")
    message_ts = f"{compact_ts[:-6]}.{compact_ts[-6:]}"
    query_ts = parse_qs(parsed.query).get("thread_ts", [message_ts])[0]
    if not re.fullmatch(r"\d+\.\d+", query_ts):
        raise ValueError("The Slack thread timestamp is invalid")
    return SlackThreadReference(channel_id=channel_id, thread_ts=query_ts)


def load_slack_thread(
    *,
    client: SlackRepliesClient,
    permalink: str,
    request_channel_id: str,
) -> DocumentPayload:
    reference = parse_slack_permalink(permalink)
    if reference.channel_id != request_channel_id:
        raise PermissionError(
            "For safety, ingest a Slack thread from the channel where that thread lives."
        )

    messages: list[dict[str, Any]] = []
    cursor: str | None = None
    while True:
        response = client.conversations_replies(
            channel=reference.channel_id,
            ts=reference.thread_ts,
            limit=200,
            cursor=cursor,
        )
        messages.extend(response.get("messages", []))
        cursor = response.get("response_metadata", {}).get("next_cursor") or None
        if not cursor:
            break

    rendered = []
    for message in messages:
        text = (message.get("text") or "").strip()
        if not text:
            continue
        author = message.get("user") or message.get("bot_id") or "unknown"
        rendered.append(f"{author} at {message.get('ts', 'unknown time')}:\n{text}")
    if not rendered:
        raise ValueError("No readable messages were found in that Slack thread")

    return DocumentPayload(
        title=f"Slack thread {reference.channel_id} {reference.thread_ts}",
        source_type="slack_thread",
        content="\n\n".join(rendered),
        source_url=permalink,
        metadata={
            "channel_id": reference.channel_id,
            "thread_ts": reference.thread_ts,
            "message_count": len(rendered),
        },
    )
