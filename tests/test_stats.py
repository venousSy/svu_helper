
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from database.connection import Database
from database.repositories import StatsRepository
from utils.enums import ProjectStatus

@pytest.mark.asyncio
async def test_get_statistics():
    # Setup Mock DB
    mock_db = AsyncMock()
    
    # Mock the aggregation pipeline result
    mock_cursor = AsyncMock()
    mock_cursor.to_list.return_value = [{
        "total": [{"count": 10}],
        "pending": [{"count": 3}],
        "active": [{"count": 4}],
        "finished": [{"count": 2}],
        "denied": [{"count": 1}]
    }]
    mock_db.projects.aggregate = MagicMock(return_value=mock_cursor)
    
    Database.db = mock_db
    
    stats = await StatsRepository.get_stats()
    
    assert stats['total'] == 10
    assert stats['pending'] == 3
    assert stats['active'] == 4
    assert stats['finished'] == 2
