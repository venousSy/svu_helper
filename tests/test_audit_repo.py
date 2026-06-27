import pytest
from unittest.mock import AsyncMock, MagicMock
from infrastructure.repositories.audit import AuditRepository
from domain.enums import AuditEventType

@pytest.fixture
def mock_db():
    db = MagicMock()
    db.audit_logs.insert_one = AsyncMock()
    cursor = AsyncMock()
    cursor.to_list = AsyncMock(return_value=[{"id": "1", "event_type": "ticket_opened"}])
    db.audit_logs.find.return_value.sort.return_value = cursor
    return db

@pytest.mark.asyncio
async def test_log_event(mock_db):
    repo = AuditRepository(mock_db)
    await repo.log_event(
        user_id=1,
        role="student",
        event_type=AuditEventType.TICKET_OPENED,
        entity_id=10,
        metadata={"a": 1}
    )
    mock_db.audit_logs.insert_one.assert_called_once()
    args, kwargs = mock_db.audit_logs.insert_one.call_args
    doc = args[0]
    assert doc["user_id"] == 1
    assert doc["role"] == "student"
    assert doc["event_type"] == AuditEventType.TICKET_OPENED.value
    assert doc["entity_id"] == 10
    assert doc["metadata"] == {"a": 1}

@pytest.mark.asyncio
async def test_get_logs_for_entity(mock_db):
    repo = AuditRepository(mock_db)
    result = await repo.get_logs_for_entity(10)
    assert len(result) == 1
    assert result[0]["id"] == "1"
    mock_db.audit_logs.find.assert_called_once_with({"entity_id": 10})
