import pytest

from slack_kb.ingestion import IngestionService
from slack_kb.models import DocumentPayload, KnowledgeScope, RequestContext


def test_non_admin_cannot_publish_org_knowledge() -> None:
    service = IngestionService(None, None, org_admin_user_ids={"U_ADMIN"})
    with pytest.raises(PermissionError):
        service.ingest(
            context=RequestContext("T1", "U_MEMBER", "C1", "thread"),
            scope=KnowledgeScope.ORG,
            payload=DocumentPayload("Title", "text", "Content"),
        )
