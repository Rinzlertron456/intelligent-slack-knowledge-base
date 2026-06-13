from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class KnowledgeScope(StrEnum):
    PERSONAL = "personal"
    TEAM = "team"
    ORG = "org"


@dataclass(frozen=True)
class RequestContext:
    workspace_id: str
    user_id: str
    channel_id: str
    thread_key: str


@dataclass(frozen=True)
class DocumentPayload:
    title: str
    source_type: str
    content: str
    source_url: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RetrievalHit:
    chunk_id: str
    document_id: str
    title: str
    content: str
    source_url: str | None
    tags: list[str]
    similarity: float
    score: float


@dataclass(frozen=True)
class AnswerResult:
    answer: str
    hits: list[RetrievalHit]
    refused: bool
