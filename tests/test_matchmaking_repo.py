import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from infrastructure.repositories.matchmaking import TeamRequestRepository

@pytest.fixture
def mock_db():
    db = MagicMock()
    db.team_requests.insert_one = AsyncMock()
    db.team_requests.find_one = AsyncMock()
    db.team_requests.update_one = AsyncMock()
    db.team_requests.delete_one = AsyncMock()
    
    cursor = MagicMock()
    cursor.sort.return_value = cursor
    cursor.to_list = AsyncMock(return_value=[{"id": 1}])
    db.team_requests.find.return_value = cursor
    return db

@pytest.mark.asyncio
@patch("infrastructure.repositories.matchmaking.Database")
async def test_create_team_request(mock_database, mock_db):
    mock_database.get_next_sequence = AsyncMock(return_value=1)
    repo = TeamRequestRepository(mock_db)
    
    req_id = await repo.create_team_request(
        host_id=1, host_name="n", host_username="u", course_name="c", doctor_name="d", specialization="s", required_members=3
    )
    assert req_id == 1
    mock_db.team_requests.insert_one.assert_called_once()

@pytest.mark.asyncio
async def test_get_by_id(mock_db):
    repo = TeamRequestRepository(mock_db)
    await repo.get_by_id(1)
    mock_db.team_requests.find_one.assert_called_with({"id": 1})

@pytest.mark.asyncio
async def test_get_open_teams_for_specialization(mock_db):
    repo = TeamRequestRepository(mock_db)
    await repo.get_open_teams_for_specialization("IT", 123)
    mock_db.team_requests.find.assert_called_once()

@pytest.mark.asyncio
async def test_add_join_request(mock_db):
    repo = TeamRequestRepository(mock_db)
    await repo.add_join_request(1, 123, "name")
    mock_db.team_requests.update_one.assert_called_once()

@pytest.mark.asyncio
async def test_update_join_request_status(mock_db):
    repo = TeamRequestRepository(mock_db)
    await repo.update_join_request_status(1, 123, "accepted")
    mock_db.team_requests.update_one.assert_called_once()

@pytest.mark.asyncio
async def test_add_member(mock_db):
    repo = TeamRequestRepository(mock_db)
    await repo.add_member(1, 123)
    mock_db.team_requests.update_one.assert_called_once()

@pytest.mark.asyncio
async def test_close_delete_request(mock_db):
    repo = TeamRequestRepository(mock_db)
    await repo.close_request(1)
    mock_db.team_requests.update_one.assert_called_once()
    await repo.delete_request(1)
    mock_db.team_requests.delete_one.assert_called_once()

@pytest.mark.asyncio
async def test_atomic_accept_member(mock_db):
    repo = TeamRequestRepository(mock_db)
    
    # modified
    mock_db.team_requests.update_one.return_value.modified_count = 1
    assert await repo.atomic_accept_member(1, 123) is True
    
    # not modified
    mock_db.team_requests.update_one.return_value.modified_count = 0
    assert await repo.atomic_accept_member(1, 123) is False

@pytest.mark.asyncio
async def test_get_user_lists(mock_db):
    repo = TeamRequestRepository(mock_db)
    await repo.get_user_open_requests(1)
    await repo.get_user_completed_requests(1)
    await repo.get_user_pending_joins(1)
    assert mock_db.team_requests.find.call_count == 3

@pytest.mark.asyncio
async def test_remove_join_request(mock_db):
    repo = TeamRequestRepository(mock_db)
    await repo.remove_join_request(1, 123)
    mock_db.team_requests.update_one.assert_called_once()

@pytest.mark.asyncio
async def test_boolean_checks(mock_db):
    repo = TeamRequestRepository(mock_db)
    mock_db.team_requests.find_one.return_value = {"id": 1}
    assert await repo.has_join_request(1, 1) is True
    assert await repo.has_global_open_team_for_subject("c", "d") is True
    assert await repo.has_active_involvement_for_course(1, "c") is True
    
    mock_db.team_requests.find_one.return_value = None
    assert await repo.has_join_request(1, 1) is False

@pytest.mark.asyncio
async def test_reject_all_pending_joins(mock_db):
    repo = TeamRequestRepository(mock_db)
    await repo.reject_all_pending_joins(1)
    mock_db.team_requests.update_one.assert_called_once()
