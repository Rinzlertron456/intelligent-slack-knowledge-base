from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from psycopg import Error as PostgresError

from slack_kb import __version__
from slack_kb.config import get_settings
from slack_kb.database import Database


# ---------------------------------------------------------------------------
# System endpoints
# ---------------------------------------------------------------------------


def service_info() -> dict[str, str]:
    return {
        "service": "intelligent-slack-knowledge-base",
        "version": __version__,
    }


def health() -> dict[str, str]:
    return {"status": "ok"}


def readiness() -> dict[str, str]:
    settings = get_settings()
    database = Database(settings.database_url.get_secret_value())
    try:
        database.open()
        with database.pool.connection() as connection:
            connection.execute("select 1").fetchone()
    except (PostgresError, TimeoutError, ValueError) as error:
        raise HTTPException(status_code=503, detail="database unavailable") from error
    finally:
        database.close()
    return {"status": "ready"}


# ---------------------------------------------------------------------------
# Admin / dashboard endpoints
# ---------------------------------------------------------------------------


def _admin_db() -> Database:
    """Return an ephemeral Database connection for admin queries."""
    settings = get_settings()
    db = Database(settings.database_url.get_secret_value())
    db.open()
    return db


def admin_stats() -> dict[str, Any]:
    """Aggregate statistics for the dashboard."""
    db = _admin_db()
    try:
        with db.pool.connection() as conn:
            doc_row = conn.execute(
                "select count(*) as total from public.documents"
            ).fetchone()
            chunk_row = conn.execute(
                "select count(*) as total from public.chunks"
            ).fetchone()
            scope_rows = conn.execute(
                "select scope, count(*) as cnt from public.documents group by scope"
            ).fetchall()
            job_row = conn.execute(
                "select count(*) as total from public.ingestion_jobs"
            ).fetchone()
            failed_row = conn.execute(
                "select count(*) as total from public.ingestion_jobs where status = 'failed'"
            ).fetchone()
        return {
            "documents": doc_row["total"] if doc_row else 0,
            "chunks": chunk_row["total"] if chunk_row else 0,
            "scopes": {r["scope"]: r["cnt"] for r in scope_rows},
            "ingestion_jobs": job_row["total"] if job_row else 0,
            "failed_jobs": failed_row["total"] if failed_row else 0,
        }
    finally:
        db.close()


def admin_documents(
    scope: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    """List documents with optional scope filter."""
    db = _admin_db()
    try:
        with db.pool.connection() as conn:
            if scope:
                rows = conn.execute(
                    """
                    select id, workspace_id, title, scope, scope_id, owner_user_id,
                           source_type, source_url, tags, status, created_by, created_at
                    from public.documents
                    where scope = %s
                    order by created_at desc
                    limit %s offset %s
                    """,
                    (scope, limit, offset),
                ).fetchall()
                count_row = conn.execute(
                    "select count(*) as total from public.documents where scope = %s",
                    (scope,),
                ).fetchone()
            else:
                rows = conn.execute(
                    """
                    select id, workspace_id, title, scope, scope_id, owner_user_id,
                           source_type, source_url, tags, status, created_by, created_at
                    from public.documents
                    order by created_at desc
                    limit %s offset %s
                    """,
                    (limit, offset),
                ).fetchall()
                count_row = conn.execute(
                    "select count(*) as total from public.documents"
                ).fetchone()
        return {
            "total": count_row["total"] if count_row else 0,
            "documents": [
                {**r, "id": str(r["id"]), "created_at": str(r["created_at"])}
                for r in rows
            ],
        }
    finally:
        db.close()


def admin_document_detail(document_id: str) -> dict[str, Any]:
    """Single document with its chunks."""
    db = _admin_db()
    try:
        with db.pool.connection() as conn:
            doc = conn.execute(
                """
                select id, workspace_id, title, scope, scope_id, owner_user_id,
                       source_type, source_url, content_hash, tags, metadata,
                       status, created_by, created_at, updated_at
                from public.documents where id = %s
                """,
                (document_id,),
            ).fetchone()
            if not doc:
                raise HTTPException(status_code=404, detail="document not found")
            chunks = conn.execute(
                """
                select id, chunk_index, content, token_estimate, created_at
                from public.chunks where document_id = %s
                order by chunk_index
                """,
                (document_id,),
            ).fetchall()
        return {
            "document": {
                **doc,
                "id": str(doc["id"]),
                "created_at": str(doc["created_at"]),
                "updated_at": str(doc["updated_at"]),
            },
            "chunks": [
                {
                    "id": str(c["id"]),
                    "chunk_index": c["chunk_index"],
                    "content": c["content"],
                    "token_estimate": c["token_estimate"],
                    "created_at": str(c["created_at"]),
                }
                for c in chunks
            ],
        }
    finally:
        db.close()


def admin_ingestion_jobs(
    limit: int = Query(50, ge=1, le=200),
) -> dict[str, Any]:
    """Recent ingestion jobs."""
    db = _admin_db()
    try:
        with db.pool.connection() as conn:
            rows = conn.execute(
                """
                select id, workspace_id, requested_by, source_label, status,
                       document_id, error_message, created_at, completed_at
                from public.ingestion_jobs
                order by created_at desc
                limit %s
                """,
                (limit,),
            ).fetchall()
        return {
            "jobs": [
                {
                    **r,
                    "id": str(r["id"]),
                    "document_id": str(r["document_id"]) if r["document_id"] else None,
                    "created_at": str(r["created_at"]),
                    "completed_at": str(r["completed_at"]) if r["completed_at"] else None,
                }
                for r in rows
            ],
        }
    finally:
        db.close()


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

Lifespan = Callable[[FastAPI], AbstractAsyncContextManager[None]]


def create_app(*, lifespan: Lifespan | None = None) -> FastAPI:
    application = FastAPI(
        title="Intelligent Slack Knowledge Base",
        version=__version__,
        description="Operational API for the Slack-native knowledge assistant.",
        lifespan=lifespan,
    )

    # CORS — allow the Vercel dashboard to call the Cloud Run backend
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["GET", "OPTIONS"],
        allow_headers=["*"],
    )

    # System routes
    application.add_api_route("/", service_info, methods=["GET"], tags=["system"])
    application.add_api_route("/healthz", health, methods=["GET"], tags=["system"])
    application.add_api_route("/readyz", readiness, methods=["GET"], tags=["system"])

    # Admin / dashboard routes
    application.add_api_route("/api/stats", admin_stats, methods=["GET"], tags=["admin"])
    application.add_api_route(
        "/api/documents", admin_documents, methods=["GET"], tags=["admin"]
    )
    application.add_api_route(
        "/api/documents/{document_id}", admin_document_detail, methods=["GET"], tags=["admin"]
    )
    application.add_api_route(
        "/api/ingestion-jobs", admin_ingestion_jobs, methods=["GET"], tags=["admin"]
    )
    return application


app = create_app()


def run() -> None:
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "slack_kb.api:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
    )


if __name__ == "__main__":
    run()
