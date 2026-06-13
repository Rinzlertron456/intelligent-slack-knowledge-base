import pytest

from slack_kb.slack_threads import (
    is_slack_permalink,
    load_slack_thread,
    parse_slack_permalink,
)


class FakeSlackClient:
    def conversations_replies(self, **kwargs):
        return {
            "messages": [
                {"user": "U1", "ts": "1710000000.000001", "text": "Decision: use Postgres."},
                {"user": "U2", "ts": "1710000001.000002", "text": "Approved."},
            ],
            "response_metadata": {"next_cursor": ""},
        }


def test_parse_slack_permalink() -> None:
    reference = parse_slack_permalink(
        "https://acme.slack.com/archives/C123/p1710000000000001"
        "?thread_ts=1710000000.000001"
    )
    assert reference.channel_id == "C123"
    assert reference.thread_ts == "1710000000.000001"


def test_identifies_slack_permalink() -> None:
    assert is_slack_permalink("https://acme.slack.com/archives/C123/p1710000000000001")
    assert not is_slack_permalink("https://example.com/thread")


def test_thread_must_be_ingested_from_same_channel() -> None:
    with pytest.raises(PermissionError):
        load_slack_thread(
            client=FakeSlackClient(),
            permalink="https://acme.slack.com/archives/C123/p1710000000000001",
            request_channel_id="C999",
        )


def test_loads_thread_as_document() -> None:
    payload = load_slack_thread(
        client=FakeSlackClient(),
        permalink="https://acme.slack.com/archives/C123/p1710000000000001",
        request_channel_id="C123",
    )
    assert payload.source_type == "slack_thread"
    assert "Decision: use Postgres." in payload.content
    assert payload.metadata["message_count"] == 2
