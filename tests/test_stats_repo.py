import pytest
from unittest.mock import AsyncMock, MagicMock
from infrastructure.repositories.stats import StatsRepository

@pytest.fixture
def mock_db():
    db = MagicMock()
    cursor = AsyncMock()
    cursor.to_list = AsyncMock(return_value=[])
    db.projects.aggregate.return_value = cursor
    return db

@pytest.mark.asyncio
async def test_get_stats_empty(mock_db):
    repo = StatsRepository(mock_db)
    res = await repo.get_stats()
    assert res == {"total": 0, "pending": 0, "active": 0, "finished": 0, "denied": 0}

@pytest.mark.asyncio
async def test_get_stats_data(mock_db):
    repo = StatsRepository(mock_db)
    mock_db.projects.aggregate.return_value.to_list.return_value = [{
        "total": [{"count": 10}],
        "pending": [{"count": 2}],
        "active": [{"count": 3}],
        "finished": [{"count": 4}],
        "denied": [{"count": 1}],
    }]
    res = await repo.get_stats()
    assert res["total"] == 10
    assert res["pending"] == 2
    assert res["active"] == 3
    assert res["finished"] == 4
    assert res["denied"] == 1
