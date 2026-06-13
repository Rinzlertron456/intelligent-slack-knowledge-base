from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from pgvector import Vector
from pgvector.psycopg import register_vector
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from slack_kb.chunking import token_estimate
from slack_kb.models import (
    DocumentPayload,
    KnowledgeScope,
    RequestContext,
    RetrievalHit,
)
from slack_kb.security import validate_scope


class Database:
    def __init__(self, database_url: str):
        self.pool = ConnectionPool(
            conninfo=database_url,
            min_size=1,
            max_size=8,
            kwargs={"row_factory": dict_row, "autocommit": True},
            configure=register_vector,
            open=False,
        )

    def open(self) -> None:
        self.pool.open(wait=True)

    def close(self) -> None:
        self.pool.close()

    def migrate(self, migration_dir: Path) -> None:
        with self.pool.connection() as connection:
            for path in sorted(migration_dir.glob("*.sql")):
                connection.execute(path.read_text(encoding="utf-8"))

    def save_document(
        self,
        *,
        context: RequestContext,
        scope: KnowledgeScope,
        payload: DocumentPayload,
        tags: list[str],
        chunks: list[str],
        embeddings: list[list[float]],
    ) -> str:
        owner_user_id, scope_id = validate_scope(
            scope,
            user_id=context.user_id,
            channel_id=context.channel_id,
        )
        content_hash = hashlib.sha256(payload.content.encode("utf-8")).hexdigest()
        with self.pool.connection() as connection, connection.transaction():
                existing = connection.execute(
                    """
                    select id from public.documents
                    where workspace_id = %s and content_hash = %s and scope = %s
                      and owner_user_id is not distinct from %s
                      and scope_id is not distinct from %s
                    """,
                    (
                        context.workspace_id,
                        content_hash,
                        scope.value,
                        owner_user_id,
                        scope_id,
                    ),
                ).fetchone()
                if existing:
                    return str(existing["id"])

                row = connection.execute(
                    """
                    insert into public.documents (
                      workspace_id, owner_user_id, scope, scope_id, title, source_type,
                      source_url, content_hash, tags, metadata, created_by
                    )
                    values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s)
                    returning id
                    """,
                    (
                        context.workspace_id,
                        owner_user_id,
                        scope.value,
                        scope_id,
                        payload.title,
                        payload.source_type,
                        payload.source_url,
                        content_hash,
                        tags,
                        json.dumps(payload.metadata),
                        context.user_id,
                    ),
                ).fetchone()
                document_id = str(row["id"])
                with connection.cursor() as cursor:
                    cursor.executemany(
                        """
                        insert into public.chunks (
                          document_id, workspace_id, chunk_index, content, token_estimate,
                          embedding, metadata
                        )
                        values (%s, %s, %s, %s, %s, %s, %s::jsonb)
                        """,
                        [
                            (
                                document_id,
                                context.workspace_id,
                                index,
                                chunk,
                                token_estimate(chunk),
                                Vector(embedding),
                                json.dumps({"title": payload.title}),
                            )
                            for index, (chunk, embedding) in enumerate(
                                zip(chunks, embeddings, strict=True)
                            )
                        ],
                    )
                return document_id

    def search(
        self,
        *,
        context: RequestContext,
        question: str,
        embedding: list[float],
        min_similarity: float,
        limit: int,
    ) -> list[RetrievalHit]:
        with self.pool.connection() as connection:
            rows = connection.execute(
                """
                select * from public.match_authorized_chunks(
                  %s::extensions.vector,
                  %s::text,
                  %s::text,
                  %s::text,
                  %s::text,
                  %s::double precision,
                  %s::integer
                )
                """,
                (
                    Vector(embedding),
                    question,
                    context.workspace_id,
                    context.user_id,
                    context.channel_id,
                    min_similarity,
                    limit,
                ),
            ).fetchall()
        return [
            RetrievalHit(
                chunk_id=str(row["chunk_id"]),
                document_id=str(row["document_id"]),
                title=row["title"],
                content=row["content"],
                source_url=row["source_url"],
                tags=list(row["tags"] or []),
                similarity=float(row["similarity"]),
                score=float(row["score"]),
            )
            for row in rows
        ]

    def add_message(self, context: RequestContext, role: str, content: str) -> None:
        with self.pool.connection() as connection:
            connection.execute(
                """
                insert into public.conversation_messages (
                  workspace_id, channel_id, thread_key, user_id, role, content
                ) values (%s, %s, %s, %s, %s, %s)
                """,
                (
                    context.workspace_id,
                    context.channel_id,
                    context.thread_key,
                    context.user_id,
                    role,
                    content,
                ),
            )

    def history(self, context: RequestContext, limit: int = 6) -> list[tuple[str, str]]:
        with self.pool.connection() as connection:
            rows = connection.execute(
                """
                select role, content
                from public.conversation_messages
                where workspace_id = %s and channel_id = %s and thread_key = %s
                  and user_id = %s
                order by created_at desc
                limit %s
                """,
                (
                    context.workspace_id,
                    context.channel_id,
                    context.thread_key,
                    context.user_id,
                    limit,
                ),
            ).fetchall()
        return [(row["role"], row["content"]) for row in reversed(rows)]

    def get_document_for_user(
        self,
        *,
        context: RequestContext,
        document_id: str,
    ) -> dict[str, Any] | None:
        with self.pool.connection() as connection:
            document = connection.execute(
                """
                select id, title, source_url, scope, owner_user_id, scope_id
                from public.documents
                where id = %s and workspace_id = %s and status = 'ready'
                  and (
                    scope = 'org'
                    or (scope = 'personal' and owner_user_id = %s)
                    or (scope = 'team' and scope_id = %s)
                  )
                """,
                (
                    document_id,
                    context.workspace_id,
                    context.user_id,
                    context.channel_id,
                ),
            ).fetchone()
            if not document:
                return None
            chunks = connection.execute(
                """
                select content from public.chunks
                where document_id = %s order by chunk_index
                """,
                (document_id,),
            ).fetchall()
        return {**document, "content": "\n\n".join(row["content"] for row in chunks)}

    def recent_documents(self, context: RequestContext, limit: int = 10) -> list[dict[str, Any]]:
        with self.pool.connection() as connection:
            return list(
                connection.execute(
                    """
                    select id, title, scope, tags, created_at
                    from public.documents
                    where workspace_id = %s
                      and (
                        scope = 'org'
                        or (scope = 'personal' and owner_user_id = %s)
                        or (scope = 'team' and scope_id = %s)
                      )
                    order by created_at desc
                    limit %s
                    """,
                    (
                        context.workspace_id,
                        context.user_id,
                        context.channel_id,
                        limit,
                    ),
                ).fetchall()
            )
