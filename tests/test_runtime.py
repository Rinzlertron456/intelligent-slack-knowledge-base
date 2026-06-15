from unittest.mock import Mock

from slack_kb.config import Settings
from slack_kb.database import configure_connection
from slack_kb.runtime import build_slack_runtime


def test_pool_configures_extension_search_path_before_vector_registration(
    monkeypatch,
) -> None:
    events: list[str] = []
    connection = Mock()
    connection.execute.side_effect = lambda _sql: events.append("search-path")
    monkeypatch.setattr(
        "slack_kb.database.register_vector",
        lambda _connection: events.append("register-vector"),
    )

    configure_connection(connection)

    assert events == ["search-path", "register-vector"]
    connection.execute.assert_called_once_with(
        "set search_path to public, extensions"
    )


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
