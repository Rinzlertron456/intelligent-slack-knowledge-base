from slack_kb.answer_graph import REFUSAL, AnswerGraph, AnswerState
from slack_kb.models import RequestContext, RetrievalHit


def state(answer: str) -> AnswerState:
    return {
        "context": RequestContext("T1", "U1", "C1", "1.0"),
        "question": "Question?",
        "history": [],
        "hits": [
            RetrievalHit("c1", "d1", "Doc", "Evidence", None, [], 0.9, 0.9),
        ],
        "answer": answer,
        "refused": False,
    }


def test_valid_citation_passes() -> None:
    assert AnswerGraph._validate(state("Answer [1].")) == {"refused": False}


def test_missing_citation_refuses() -> None:
    result = AnswerGraph._validate(state("Unsupported answer."))
    assert result == {"answer": REFUSAL, "refused": True}


def test_unknown_citation_refuses() -> None:
    result = AnswerGraph._validate(state("Answer [2]."))
    assert result == {"answer": REFUSAL, "refused": True}
