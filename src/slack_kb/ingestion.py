from __future__ import annotations

from slack_kb.chunking import chunk_text
from slack_kb.database import Database
from slack_kb.models import DocumentPayload, KnowledgeScope, RequestContext
from slack_kb.openai_service import OpenAIService


class IngestionService:
    def __init__(
        self,
        database: Database,
        openai: OpenAIService,
        *,
        org_admin_user_ids: set[str] | None = None,
    ):
        self.database = database
        self.openai = openai
        self.org_admin_user_ids = org_admin_user_ids or set()

    def ingest(
        self,
        *,
        context: RequestContext,
        scope: KnowledgeScope,
        payload: DocumentPayload,
    ) -> str:
        if (
            scope is KnowledgeScope.ORG
            and context.user_id not in self.org_admin_user_ids
        ):
            raise PermissionError(
                "Only configured organisation knowledge admins may add org-wide content."
            )
        chunks = chunk_text(payload.content)
        if not chunks:
            raise ValueError("No indexable text was found")
        embeddings: list[list[float]] = []
        for start in range(0, len(chunks), 64):
            embeddings.extend(self.openai.embed(chunks[start : start + 64]))
        tags = self.openai.auto_tags(title=payload.title, content=payload.content)
        return self.database.save_document(
            context=context,
            scope=scope,
            payload=payload,
            tags=tags,
            chunks=chunks,
            embeddings=embeddings,
        )
