from slack_kb.models import KnowledgeScope
from slack_kb.security import scope_allows, validate_scope


def test_personal_scope_is_user_isolated() -> None:
    assert scope_allows(
        scope=KnowledgeScope.PERSONAL,
        owner_user_id="U1",
        scope_id=None,
        requester_user_id="U1",
        requester_channel_id="D1",
    )
    assert not scope_allows(
        scope=KnowledgeScope.PERSONAL,
        owner_user_id="U1",
        scope_id=None,
        requester_user_id="U2",
        requester_channel_id="D1",
    )


def test_team_scope_is_channel_isolated() -> None:
    assert scope_allows(
        scope=KnowledgeScope.TEAM,
        owner_user_id=None,
        scope_id="C1",
        requester_user_id="U2",
        requester_channel_id="C1",
    )
    assert not scope_allows(
        scope=KnowledgeScope.TEAM,
        owner_user_id=None,
        scope_id="C1",
        requester_user_id="U2",
        requester_channel_id="C2",
    )


def test_team_scope_rejects_direct_messages() -> None:
    try:
        validate_scope(KnowledgeScope.TEAM, user_id="U1", channel_id="D1")
    except ValueError as error:
        assert "Slack channel" in str(error)
    else:
        raise AssertionError("Expected team scope validation to fail for a DM")
