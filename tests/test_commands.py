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
