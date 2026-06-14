import pytest

from slack_kb.commands import parse_command
from slack_kb.models import KnowledgeScope


def test_parse_add_command() -> None:
    command = parse_command("add team https://example.com")
    assert command.action == "add"
    assert command.scope is KnowledgeScope.TEAM
    assert command.argument == "https://example.com"


def test_plain_question_defaults_to_ask() -> None:
    command = parse_command("What is the leave policy?")
    assert command.action == "ask"


def test_add_accepts_attached_file_without_text() -> None:
    command = parse_command("add personal")
    assert command.action == "add"
    assert command.scope is KnowledgeScope.PERSONAL
    assert command.argument == ""


def test_add_requires_scope() -> None:
    with pytest.raises(ValueError):
        parse_command("add")


@pytest.mark.parametrize(
    "attribution",
    [
        "*Sent using* <@U0BB60SRM9N>",
        "_Sent using_ <@U0BB60SRM9N|ChatGPT>",
    ],
)
def test_trailing_app_attribution_is_ignored(attribution: str) -> None:
    command = parse_command(
        "summarize 1a63c52d-be12-45c3-a1f5-1acd474b7e6b\n" + attribution
    )

    assert command.action == "summarize"
    assert command.argument == "1a63c52d-be12-45c3-a1f5-1acd474b7e6b"


def test_inline_app_attribution_is_ignored() -> None:
    command = parse_command(
        "summarize 1a63c52d-be12-45c3-a1f5-1acd474b7e6b "
        "*Sent using* <@U0BB60SRM9N>"
    )

    assert command.argument == "1a63c52d-be12-45c3-a1f5-1acd474b7e6b"
