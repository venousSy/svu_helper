import pytest
from unittest.mock import AsyncMock, MagicMock
from application.audit_service import AuditService
from domain.enums import AuditEventType

@pytest.mark.asyncio
async def test_audit_service_log_event():
    mock_repo = AsyncMock()
    service = AuditService(mock_repo)
    
    await service.log_event(
        user_id=123,
        role="student",
        event_type=AuditEventType.PROJECT_CREATED,
        entity_id=456,
        metadata={"key": "value"}
    )
    
    mock_repo.log_event.assert_called_once_with(
        user_id=123,
        role="student",
        event_type=AuditEventType.PROJECT_CREATED,
        entity_id=456,
        metadata={"key": "value"}
    )
