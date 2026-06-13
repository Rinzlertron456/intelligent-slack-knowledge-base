from slack_kb.api import health


def test_health_endpoint() -> None:
    assert health() == {"status": "ok"}
