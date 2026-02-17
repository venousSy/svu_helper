
import pytest
from unittest.mock import AsyncMock, patch
from database.connection import Database
from database.repositories import StatsRepository
from utils.enums import ProjectStatus

@pytest.mark.asyncio
async def test_get_statistics():
    # Setup Mock DB
    mock_db = AsyncMock()
    
    # Mock count_documents to return different values based on the query
    async def mock_count_side_effect(query):
        if query == {}: return 10
        if query == {"status": ProjectStatus.PENDING}: return 3
        if "active" in str(query) or ProjectStatus.ACCEPTED in str(query): return 4
        if query == {"status": ProjectStatus.FINISHED}: return 2
        return 1 # Default for denied/others

    mock_db.projects.count_documents.side_effect = mock_count_side_effect
    
    Database.db = mock_db
    
    stats = await StatsRepository.get_stats()
    
    assert stats['total'] == 10
    assert stats['pending'] == 3
    assert stats['active'] == 4
    assert stats['finished'] == 2
