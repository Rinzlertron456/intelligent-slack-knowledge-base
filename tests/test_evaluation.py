from slack_kb.evaluation import citations_are_valid, score_case, summarize


def test_citation_validation() -> None:
    assert citations_are_valid("The policy says 21 days [1].", 1)
    assert not citations_are_valid("The policy says 21 days.", 1)
    assert not citations_are_valid("The policy says 21 days [2].", 1)


def test_acl_leak_is_reported() -> None:
    result = score_case(
        case={
            "id": "acl-1",
            "expected_outcome": "refuse",
            "acl_case": True,
        },
        answer="Leaked answer [1].",
        refused=False,
        hit_titles=["Private"],
        hit_count=1,
        latency_seconds=0.2,
    )
    assert result.acl_leak
    assert not result.grounded


def test_summary_counts_grounded_and_refusal_cases() -> None:
    answer = score_case(
        case={
            "id": "answer-1",
            "expected_outcome": "answer",
            "expected_terms": ["21"],
            "expected_source": "Policy",
        },
        answer="Employees receive 21 days [1].",
        refused=False,
        hit_titles=["Policy"],
        hit_count=1,
        latency_seconds=1.0,
    )
    refusal = score_case(
        case={"id": "refusal-1", "expected_outcome": "refuse"},
        answer="I couldn't find enough evidence.",
        refused=True,
        hit_titles=[],
        hit_count=0,
        latency_seconds=2.0,
    )
    metrics = summarize([answer, refusal])
    assert metrics["grounded_score"] == 1.0
    assert metrics["refusal_precision"] == 1.0
    assert metrics["acl_leaks"] == 0
