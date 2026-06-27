import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from infrastructure.repositories.project import ProjectRepository
from domain.enums import ProjectStatus

@pytest.fixture
def mock_db():
    db = MagicMock()
    db.projects.insert_one = AsyncMock()
    db.projects.find_one = AsyncMock()
    db.projects.update_one = AsyncMock()
    db.projects.distinct = AsyncMock()
    
    cursor = MagicMock()
    cursor.sort.return_value = cursor
    cursor.skip.return_value = cursor
    cursor.limit.return_value = cursor
    cursor.to_list = AsyncMock(return_value=[{"id": 1, "created_at": "old"}])
    
    db.projects.find.return_value = cursor
    
    cursor_agg = MagicMock()
    cursor_agg.to_list = AsyncMock(return_value=[{"id": 2, "created_at": "newer"}])
    db.projects.aggregate.return_value = cursor_agg
    return db

@pytest.mark.asyncio
@patch("infrastructure.repositories.project.Database")
async def test_add_project(mock_database, mock_db):
    mock_database.get_next_sequence = AsyncMock(return_value=1)
    repo = ProjectRepository(mock_db)
    
    project_id = await repo.add_project(
        user_id=123, username="u", user_full_name="f", subject="s", tutor="t", 
        deadline="2030-01-01", details="d", attachments=[]
    )
    assert project_id == 1
    mock_db.projects.insert_one.assert_called_once()

@pytest.mark.asyncio
async def test_get_project_by_id(mock_db):
    repo = ProjectRepository(mock_db)
    mock_db.projects.find_one.return_value = {"id": 1}
    result = await repo.get_project_by_id(1)
    assert result["id"] == 1
    mock_db.projects.find_one.assert_called_with({"id": 1})

@pytest.mark.asyncio
async def test_get_user_projects(mock_db):
    repo = ProjectRepository(mock_db)
    result = await repo.get_user_projects(123)
    assert result == [{"id": 1, "created_at": "old"}]
    mock_db.projects.find.assert_called_with({"user_id": 123})

@pytest.mark.asyncio
async def test_update_status(mock_db):
    repo = ProjectRepository(mock_db)
    await repo.update_status(1, "new_status")
    mock_db.projects.update_one.assert_called_with({"id": 1}, {"$set": {"status": "new_status"}})

@pytest.mark.asyncio
async def test_get_projects_by_status(mock_db):
    repo = ProjectRepository(mock_db)
    result = await repo.get_projects_by_status(["s1"], user_id=123)
    assert result == [{"id": 1, "created_at": "old"}]
    mock_db.projects.find.assert_called_with({"status": {"$in": ["s1"]}, "user_id": 123})

@pytest.mark.asyncio
async def test_update_offer(mock_db):
    repo = ProjectRepository(mock_db)
    await repo.update_offer(1, "100", "tmrw")
    mock_db.projects.update_one.assert_called_once()

@pytest.mark.asyncio
async def test_get_all_categorized(mock_db):
    repo = ProjectRepository(mock_db)
    mock_db.projects.find.return_value.to_list = AsyncMock(return_value=[])
    res = await repo.get_all_categorized()
    assert "New / Pending" in res
    assert "History" in res

@pytest.mark.asyncio
async def test_get_all_user_ids(mock_db):
    repo = ProjectRepository(mock_db)
    mock_db.projects.distinct.return_value = [1, 2]
    res = await repo.get_all_user_ids()
    assert res == [1, 2]

@pytest.mark.asyncio
async def test_get_urgent_projects(mock_db):
    repo = ProjectRepository(mock_db)
    res = await repo.get_urgent_projects()
    assert len(res) == 2
