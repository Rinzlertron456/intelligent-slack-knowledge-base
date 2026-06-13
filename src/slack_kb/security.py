from slack_kb.models import KnowledgeScope


def validate_scope(
    scope: KnowledgeScope,
    *,
    user_id: str,
    channel_id: str,
) -> tuple[str | None, str | None]:
    if scope is KnowledgeScope.PERSONAL:
        return user_id, None
    if scope is KnowledgeScope.TEAM:
        if not channel_id.startswith(("C", "G")):
            raise ValueError("Team knowledge must be added from a Slack channel")
        return None, channel_id
    return None, None


def scope_allows(
    *,
    scope: KnowledgeScope,
    owner_user_id: str | None,
    scope_id: str | None,
    requester_user_id: str,
    requester_channel_id: str,
) -> bool:
    if scope is KnowledgeScope.ORG:
        return True
    if scope is KnowledgeScope.PERSONAL:
        return owner_user_id == requester_user_id
    return scope_id == requester_channel_id and requester_channel_id.startswith(("C", "G"))
