import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from dashboard_api.repositories.projects_repo import count_projects, get_paginated_projects

@pytest.fixture
def mock_db():
    db = MagicMock()
    db.projects.count_documents = AsyncMock(return_value=10)
    
    cursor = MagicMock()
    cursor.sort.return_value = cursor
    cursor.skip.return_value = cursor
    cursor.limit.return_value = cursor
    cursor.to_list = AsyncMock(return_value=[{"id": 1}])
    db.projects.find.return_value = cursor
    return db

@pytest.mark.asyncio
@patch("dashboard_api.repositories.projects_repo.get_db")
async def test_count_projects(mock_get_db, mock_db):
    mock_get_db.return_value = mock_db
    assert await count_projects("s", 1) == 10
    mock_db.projects.count_documents.assert_called_with({"status": "s", "user_id": 1})
    
    await count_projects()
    mock_db.projects.count_documents.assert_called_with({})

@pytest.mark.asyncio
@patch("dashboard_api.repositories.projects_repo.get_db")
async def test_get_paginated_projects(mock_get_db, mock_db):
    mock_get_db.return_value = mock_db
    res = await get_paginated_projects(0, 5, "s", 1)
    assert res == [{"id": 1}]
    mock_db.projects.find.assert_called_with({"status": "s", "user_id": 1})
    
    await get_paginated_projects(0, 5)
    mock_db.projects.find.assert_called_with({})
