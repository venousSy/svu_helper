
import pytest
from unittest.mock import AsyncMock, patch
from database import get_statistics, Database, STATUS_PENDING, STATUS_ACCEPTED, STATUS_FINISHED

@pytest.mark.asyncio
async def test_get_statistics():
    # Setup Mock DB
    mock_db = AsyncMock()
    
    # Mock count_documents to return different values based on the query
    async def mock_count_side_effect(query):
        if query == {}: return 10
        if query == {"status": STATUS_PENDING}: return 3
        if "active" in str(query) or STATUS_ACCEPTED in str(query): return 4
        if query == {"status": STATUS_FINISHED}: return 2
        return 1 # Default for denied/others

    mock_db.projects.count_documents.side_effect = mock_count_side_effect
    
    with patch('database.get_db', return_value=mock_db):
        Database.db = mock_db
        
        stats = await get_statistics()
        
        assert stats['total'] == 10
        assert stats['pending'] == 3
        assert stats['active'] == 4
        assert stats['finished'] == 2
