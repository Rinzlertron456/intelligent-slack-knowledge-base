from __future__ import annotations

import json
import math
import time
from uuid import uuid4

from slack_kb.config import get_settings
from slack_kb.database import Database
from slack_kb.models import DocumentPayload, KnowledgeScope, RequestContext


def percentile(values: list[float], percentile_value: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, math.ceil(len(ordered) * percentile_value) - 1)
    return ordered[index]


def run(document_count: int = 60, query_count: int = 20) -> dict[str, float | int]:
    settings = get_settings()
    if settings.embedding_dimensions < document_count:
        raise ValueError("Embedding dimensions must be at least the document count")

    database = Database(settings.database_url.get_secret_value())
    database.open()
    workspace_id = f"scale-smoke-{uuid4()}"
    context = RequestContext(
        workspace_id=workspace_id,
        user_id="U-SCALE-OWNER",
        channel_id="C-SCALE-TEAM",
        thread_key="scale-smoke",
    )

    document_ids: list[str] = []
    started = time.perf_counter()
    try:
        for index in range(document_count):
            embedding = [0.0] * settings.embedding_dimensions
            embedding[index] = 1.0
            document_ids.append(
                database.save_document(
                    context=context,
                    scope=KnowledgeScope.TEAM,
                    payload=DocumentPayload(
                        title=f"Scale policy {index:02d}",
                        source_type="scale-smoke",
                        content=(
                            f"Scale policy {index:02d} has verification code "
                            f"SCALE-{index:02d}-READY."
                        ),
                    ),
                    tags=["scale-smoke"],
                    chunks=[
                        f"Scale policy {index:02d} has verification code "
                        f"SCALE-{index:02d}-READY."
                    ],
                    embeddings=[embedding],
                )
            )

        ingest_seconds = time.perf_counter() - started
        latencies: list[float] = []
        for target in range(query_count):
            embedding = [0.0] * settings.embedding_dimensions
            embedding[target] = 1.0
            query_started = time.perf_counter()
            hits = database.search(
                context=context,
                question=f"What is the verification code for scale policy {target:02d}?",
                embedding=embedding,
                min_similarity=0.99,
                limit=1,
            )
            latencies.append(time.perf_counter() - query_started)
            if not hits or hits[0].document_id != document_ids[target]:
                raise RuntimeError(f"Scale retrieval failed for document {target}")

        report: dict[str, float | int] = {
            "documents": document_count,
            "queries": query_count,
            "ingest_seconds": round(ingest_seconds, 3),
            "query_p50_seconds": round(percentile(latencies, 0.50), 4),
            "query_p95_seconds": round(percentile(latencies, 0.95), 4),
            "retrieval_accuracy": 1.0,
        }
        if report["query_p95_seconds"] >= 10:
            raise RuntimeError("Scale retrieval p95 exceeded 10 seconds")
        return report
    finally:
        database.purge_workspace(workspace_id)
        database.close()


def main() -> None:
    print(json.dumps(run(), indent=2))


if __name__ == "__main__":
    main()
