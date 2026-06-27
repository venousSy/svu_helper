import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from infrastructure.mongo_db import Database, get_db, init_db

@pytest.fixture
def reset_db():
    original_client = Database.client
    original_db = Database.db
    Database.client = MagicMock()
    
    mock_db = MagicMock()
    mock_db.projects.create_index = AsyncMock()
    mock_db.payments.create_index = AsyncMock()
    mock_db.fsm_states.create_index = AsyncMock()
    mock_db.tickets.create_index = AsyncMock()
    mock_db.tickets.drop_index = AsyncMock()
    mock_db.tickets.update_many = AsyncMock()
    mock_db.team_requests.create_index = AsyncMock()
    
    mock_db.counters.find_one_and_update = AsyncMock()
    
    Database.client.__getitem__.return_value = mock_db
    Database.db = None
    
    yield mock_db
    
    Database.client = original_client
    Database.db = original_db

@pytest.mark.asyncio
async def test_connect(reset_db):
    await Database.connect()
    assert Database.db is not None
    reset_db.projects.create_index.assert_called()
    reset_db.payments.create_index.assert_called()
    reset_db.tickets.drop_index.assert_called_with("message_thread_id_1")

@pytest.mark.asyncio
async def test_connect_drop_index_fails(reset_db):
    reset_db.tickets.drop_index.side_effect = Exception("not found")
    await Database.connect()
    assert Database.db is not None
    reset_db.tickets.create_index.assert_called()

@pytest.mark.asyncio
async def test_get_next_sequence(reset_db):
    reset_db.counters.find_one_and_update.return_value = {"seq": 5}
    seq = await Database.get_next_sequence("test_seq")
    assert seq == 5
    reset_db.counters.find_one_and_update.assert_called_once()

@pytest.mark.asyncio
async def test_get_db(reset_db):
    db = await get_db()
    assert db is not None
    
    # second call should return same without reconnect
    db2 = await get_db()
    assert db2 is db

@pytest.mark.asyncio
async def test_init_db(reset_db):
    await init_db()
    assert Database.db is not None
