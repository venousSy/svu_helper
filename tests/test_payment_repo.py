import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from infrastructure.repositories.payment import PaymentRepository

@pytest.fixture
def mock_db():
    db = MagicMock()
    db.payments.insert_one = AsyncMock()
    db.payments.find_one = AsyncMock()
    db.payments.update_one = AsyncMock()
    
    cursor = MagicMock()
    cursor.to_list = AsyncMock(return_value=[{"id": 1}])
    db.payments.aggregate.return_value = cursor
    return db

@pytest.mark.asyncio
@patch("infrastructure.repositories.payment.Database")
async def test_add_payment(mock_database, mock_db):
    mock_database.get_next_sequence = AsyncMock(return_value=1)
    repo = PaymentRepository(mock_db)
    
    payment_id = await repo.add_payment(project_id=10, user_id=123, file_id="f1", file_type="photo")
    assert payment_id == 1
    mock_db.payments.insert_one.assert_called_once()
    args, _ = mock_db.payments.insert_one.call_args
    assert args[0]["project_id"] == 10

@pytest.mark.asyncio
async def test_get_payment(mock_db):
    repo = PaymentRepository(mock_db)
    mock_db.payments.find_one.return_value = {"id": 1}
    res = await repo.get_payment(1)
    assert res["id"] == 1

@pytest.mark.asyncio
async def test_get_payment_by_project_id(mock_db):
    repo = PaymentRepository(mock_db)
    mock_db.payments.find_one.return_value = {"project_id": 10}
    res = await repo.get_payment_by_project_id(10)
    assert res["project_id"] == 10

@pytest.mark.asyncio
async def test_update_status(mock_db):
    repo = PaymentRepository(mock_db)
    await repo.update_status(1, "new_status")
    mock_db.payments.update_one.assert_called_with({"id": 1}, {"$set": {"status": "new_status"}})

@pytest.mark.asyncio
async def test_get_all(mock_db):
    repo = PaymentRepository(mock_db)
    res = await repo.get_all(limit=10, skip=0)
    assert res == [{"id": 1}]
    mock_db.payments.aggregate.assert_called_once()
