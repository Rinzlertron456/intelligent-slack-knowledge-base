from unittest.mock import Mock

from slack_kb.config import Settings
from slack_kb.runtime import build_slack_runtime


def test_fresh_database_is_migrated_before_vector_pool_opens(monkeypatch) -> None:
    events: list[str] = []
    database = Mock()
    database.open.side_effect = lambda: events.append("open")

    monkeypatch.setattr(
        "slack_kb.runtime.apply_database_migrations",
        lambda *_args: events.append("migrate"),
    )
    monkeypatch.setattr("slack_kb.runtime.Database", lambda _url: database)
    monkeypatch.setattr("slack_kb.runtime.OpenAIService", Mock())
    monkeypatch.setattr("slack_kb.runtime.AnswerGraph", Mock())
    monkeypatch.setattr("slack_kb.runtime.IngestionService", Mock())
    monkeypatch.setattr("slack_kb.runtime.App", Mock())
    monkeypatch.setattr("slack_kb.runtime.SlackKnowledgeApp", Mock())
    monkeypatch.setattr("slack_kb.runtime.SocketModeHandler", Mock())

    settings = Settings(
        openai_api_key="test-openai-key",
        database_url="postgresql://example.test/slack_kb",
        slack_bot_token="xoxb-test",
        slack_app_token="xapp-test",
    )

    build_slack_runtime(settings, apply_migrations=True)

    assert events == ["migrate", "open"]
