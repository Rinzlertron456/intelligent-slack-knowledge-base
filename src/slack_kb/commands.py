from __future__ import annotations

import re
from dataclasses import dataclass

from slack_kb.models import KnowledgeScope

TRAILING_APP_ATTRIBUTION = re.compile(
    r"\s+(?:\*|_)?Sent using(?:\*|_)?\s+<@[A-Z0-9]+(?:\|[^>]+)?>\s*$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ParsedCommand:
    action: str
    argument: str = ""
    scope: KnowledgeScope | None = None


def parse_command(text: str) -> ParsedCommand:
    stripped = TRAILING_APP_ATTRIBUTION.sub("", text).strip()
    if not stripped:
        return ParsedCommand("help")
    action, _, remainder = stripped.partition(" ")
    action = action.lower()
    remainder = remainder.strip()
    if action == "add":
        raw_scope, separator, content = remainder.partition(" ")
        if not raw_scope:
            raise ValueError("Usage: add <personal|team|org> <URL, text, or attached file>")
        try:
            scope = KnowledgeScope(raw_scope.lower())
        except ValueError as error:
            raise ValueError("Scope must be personal, team, or org") from error
        return ParsedCommand(
            action="add",
            argument=content.strip() if separator else "",
            scope=scope,
        )
    if action in {"ask", "summarize"} and not remainder:
        raise ValueError(f"Usage: {action} <{'question' if action == 'ask' else 'document-id'}>")
    if action not in {"ask", "summarize", "status", "help"}:
        return ParsedCommand("ask", argument=stripped)
    return ParsedCommand(action=action, argument=remainder)
