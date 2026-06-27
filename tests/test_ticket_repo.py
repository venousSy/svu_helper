import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from infrastructure.repositories.ticket import TicketRepository
from domain.enums import TicketStatus

@pytest.fixture
def mock_db():
    db = MagicMock()
    db.tickets.insert_one = AsyncMock()
    db.tickets.find_one = AsyncMock()
    db.tickets.update_one = AsyncMock()
    db.tickets.count_documents = AsyncMock(return_value=1)
    
    cursor = MagicMock()
    cursor.sort.return_value = cursor
    cursor.skip.return_value = cursor
    cursor.limit.return_value = cursor
    cursor.to_list = AsyncMock(return_value=[{"ticket_id": 1}])
    db.tickets.find.return_value = cursor
    return db

@pytest.mark.asyncio
@patch("infrastructure.repositories.ticket.Database")
async def test_create_ticket(mock_database, mock_db):
    mock_database.get_next_sequence = AsyncMock(return_value=1)
    repo = TicketRepository(mock_db)
    
    ticket_id = await repo.create_ticket(user_id=123, initial_text="Hello")
    assert ticket_id == 1
    mock_db.tickets.insert_one.assert_called_once()
    args, _ = mock_db.tickets.insert_one.call_args
    assert args[0]["user_id"] == 123
    assert args[0]["messages"][0]["text"] == "Hello"

@pytest.mark.asyncio
async def test_get_ticket_by_id(mock_db):
    repo = TicketRepository(mock_db)
    mock_db.tickets.find_one.return_value = {"ticket_id": 1}
    res = await repo.get_ticket_by_id(1)
    assert res["ticket_id"] == 1

@pytest.mark.asyncio
async def test_get_ticket_by_thread(mock_db):
    repo = TicketRepository(mock_db)
    await repo.get_ticket_by_thread(999)
    mock_db.tickets.find_one.assert_called_with({"message_thread_id": 999})

@pytest.mark.asyncio
async def test_get_active_tickets(mock_db):
    repo = TicketRepository(mock_db)
    res = await repo.get_active_tickets(123)
    assert len(res) == 1
    mock_db.tickets.find.assert_called_with({"user_id": 123, "status": TicketStatus.OPEN})

@pytest.mark.asyncio
async def test_get_all_active_tickets(mock_db):
    repo = TicketRepository(mock_db)
    tickets, count = await repo.get_all_active_tickets(0, 5)
    assert count == 1
    assert len(tickets) == 1

@pytest.mark.asyncio
async def test_get_recent_messages(mock_db):
    repo = TicketRepository(mock_db)
    # no messages
    mock_db.tickets.find_one.return_value = None
    res = await repo.get_recent_messages(1)
    assert res == []
    
    # some messages
    mock_db.tickets.find_one.return_value = {"messages": [1, 2, 3]}
    res = await repo.get_recent_messages(1, page=0, page_size=2)
    assert res == [3, 2]

@pytest.mark.asyncio
async def test_get_message_count(mock_db):
    repo = TicketRepository(mock_db)
    mock_db.tickets.find_one.return_value = {"messages": [1, 2]}
    assert await repo.get_message_count(1) == 2
    
    mock_db.tickets.find_one.return_value = None
    assert await repo.get_message_count(1) == 0

@pytest.mark.asyncio
async def test_set_thread_id(mock_db):
    repo = TicketRepository(mock_db)
    await repo.set_thread_id(1, 999)
    mock_db.tickets.update_one.assert_called_with({"ticket_id": 1}, {"$set": {"message_thread_id": 999}})

@pytest.mark.asyncio
async def test_add_message(mock_db):
    repo = TicketRepository(mock_db)
    await repo.add_message(1, sender="user", text="hello")
    mock_db.tickets.update_one.assert_called_once()

@pytest.mark.asyncio
async def test_close_reopen_ticket(mock_db):
    repo = TicketRepository(mock_db)
    await repo.close_ticket(1)
    mock_db.tickets.update_one.assert_called_with({"ticket_id": 1}, {"$set": {"status": TicketStatus.CLOSED}})
    
    await repo.reopen_ticket(1)
    mock_db.tickets.update_one.assert_called_with({"ticket_id": 1}, {"$set": {"status": TicketStatus.OPEN}})

@pytest.mark.asyncio
async def test_get_closed_tickets(mock_db):
    repo = TicketRepository(mock_db)
    res = await repo.get_closed_tickets(123)
    assert len(res) == 1
    mock_db.tickets.find.assert_called_with({"user_id": 123, "status": TicketStatus.CLOSED})
