"""
Unit tests for StatsRepository.
Updated to use constructor-injected DI pattern.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from infrastructure.repositories import StatsRepository


@pytest.mark.asyncio
async def test_get_statistics():
    # Setup Mock DB
    mock_db = AsyncMock()

    # Mock the aggregation pipeline result
    mock_cursor = AsyncMock()
    mock_cursor.to_list.return_value = [
        {
            "total": [{"count": 10}],
            "pending": [{"count": 3}],
            "active": [{"count": 4}],
            "finished": [{"count": 2}],
            "denied": [{"count": 1}],
        }
    ]
    mock_db.projects.aggregate = MagicMock(return_value=mock_cursor)

    # Inject mock_db via constructor – no global mutation
    repo = StatsRepository(mock_db)
    stats = await repo.get_stats()

    assert stats["total"] == 10
    assert stats["pending"] == 3
    assert stats["active"] == 4
    assert stats["finished"] == 2
