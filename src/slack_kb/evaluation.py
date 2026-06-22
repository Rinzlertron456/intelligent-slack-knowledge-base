from __future__ import annotations

import argparse
import json
import re
import statistics
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from slack_kb.answer_graph import AnswerGraph
from slack_kb.config import get_settings
from slack_kb.database import Database
from slack_kb.ingestion import IngestionService
from slack_kb.models import KnowledgeScope, RequestContext
from slack_kb.gemini_service import GeminiService
from slack_kb.parsers import parse_plain_text


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    expected_outcome: str
    refused: bool
    terms_matched: bool
    expected_source_retrieved: bool
    citations_valid: bool
    grounded: bool
    acl_leak: bool
    latency_seconds: float
    answer: str


def citations_are_valid(answer: str, hit_count: int) -> bool:
    citations = [int(value) for value in re.findall(r"\[(\d+)\]", answer)]
    return bool(citations) and all(1 <= citation <= hit_count for citation in citations)


def percentile(values: list[float], percentile_value: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * percentile_value)))
    return ordered[index]


def score_case(
    *,
    case: dict[str, Any],
    answer: str,
    refused: bool,
    hit_titles: list[str],
    hit_count: int,
    latency_seconds: float,
) -> CaseResult:
    normalized_answer = answer.casefold()
    expected_terms = [term.casefold() for term in case.get("expected_terms", [])]
    terms_matched = all(term in normalized_answer for term in expected_terms)
    expected_source = case.get("expected_source")
    source_retrieved = not expected_source or expected_source in hit_titles
    citations_valid = refused or citations_are_valid(answer, hit_count)
    expects_refusal = case["expected_outcome"] == "refuse"
    grounded = (
        refused
        if expects_refusal
        else not refused and terms_matched and source_retrieved and citations_valid
    )
    return CaseResult(
        case_id=case["id"],
        expected_outcome=case["expected_outcome"],
        refused=refused,
        terms_matched=terms_matched,
        expected_source_retrieved=source_retrieved,
        citations_valid=citations_valid,
        grounded=grounded,
        acl_leak=bool(case.get("acl_case")) and not refused,
        latency_seconds=round(latency_seconds, 3),
        answer=answer,
    )


def summarize(results: list[CaseResult]) -> dict[str, Any]:
    answerable = [result for result in results if result.expected_outcome == "answer"]
    refusal_cases = [result for result in results if result.expected_outcome == "refuse"]
    latencies = [result.latency_seconds for result in results]
    grounded_count = sum(result.grounded for result in results)
    return {
        "cases": len(results),
        "grounded_score": round(grounded_count / len(results), 4) if results else 0.0,
        "answer_accuracy": round(
            sum(result.terms_matched and not result.refused for result in answerable)
            / len(answerable),
            4,
        )
        if answerable
        else 0.0,
        "citation_validity": round(
            sum(result.citations_valid and not result.refused for result in answerable)
            / len(answerable),
            4,
        )
        if answerable
        else 0.0,
        "refusal_precision": round(
            sum(result.refused for result in refusal_cases) / len(refusal_cases),
            4,
        )
        if refusal_cases
        else 0.0,
        "acl_leaks": sum(result.acl_leak for result in results),
        "latency_p50_seconds": round(statistics.median(latencies), 3) if latencies else 0.0,
        "latency_p95_seconds": round(percentile(latencies, 0.95), 3),
    }


def run(dataset_path: Path, *, limit: int | None = None) -> dict[str, Any]:
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    settings = get_settings()
    database = Database(settings.database_url.get_secret_value())
    database.open()
    run_id = uuid.uuid4().hex[:10].upper()
    workspace_id = f"T_EVAL_{run_id}"
    other_workspace_id = f"T_OTHER_{run_id}"
    results: list[CaseResult] = []

    try:
        gemini = GeminiService(settings)
        ingestion = IngestionService(
            database,
            gemini,
            org_admin_user_ids={"U_ADMIN"},
        )
        graph = AnswerGraph(database, gemini, settings)

        for document in dataset["documents"]:
            context = RequestContext(
                workspace_id=workspace_id,
                user_id=document.get("owner_user_id", "U_ADMIN"),
                channel_id=document.get("channel_id", "C_GENERAL"),
                thread_key=f"seed:{document['id']}",
            )
            ingestion.ingest(
                context=context,
                scope=KnowledgeScope(document["scope"]),
                payload=parse_plain_text(document["content"], title=document["title"]),
            )

        cases = dataset["cases"][:limit] if limit else dataset["cases"]
        for case in cases:
            context = RequestContext(
                workspace_id=(
                    other_workspace_id
                    if case.get("workspace_mode") == "other"
                    else workspace_id
                ),
                user_id=case.get("user_id", "U_TESTER"),
                channel_id=case.get("channel_id", "C_GENERAL"),
                thread_key=f"eval:{case['id']}:{run_id}",
            )
            started = time.perf_counter()
            result = graph.ask(context, case["question"])
            latency = time.perf_counter() - started
            results.append(
                score_case(
                    case=case,
                    answer=result.answer,
                    refused=result.refused,
                    hit_titles=[hit.title for hit in result.hits],
                    hit_count=len(result.hits),
                    latency_seconds=latency,
                )
            )
    finally:
        database.purge_workspace(workspace_id)
        database.purge_workspace(other_workspace_id)
        database.close()

    report = {
        "dataset": dataset["name"],
        "run_id": run_id,
        "summary": summarize(results),
        "results": [asdict(result) for result in results],
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Slack KB golden evaluation set.")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("evals/golden_dataset.json"),
    )
    parser.add_argument("--limit", type=int)
    parser.add_argument("--output", type=Path, default=Path("evals/latest-report.json"))
    parser.add_argument("--min-grounded-score", type=float, default=0.80)
    args = parser.parse_args()

    report = run(args.dataset, limit=args.limit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))

    summary = report["summary"]
    if summary["grounded_score"] < args.min_grounded_score or summary["acl_leaks"] > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
