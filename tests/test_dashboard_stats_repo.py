import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from dashboard_api.repositories.stats_repo import aggregate_project_volume, aggregate_conversion_rates, aggregate_revenue_over_time, aggregate_total_revenue

@pytest.fixture
def mock_db():
    db = MagicMock()
    cursor = MagicMock()
    cursor.to_list = AsyncMock(return_value=[{"total": 100}])
    db.projects.aggregate.return_value = cursor
    return db

@pytest.mark.asyncio
@patch("dashboard_api.repositories.stats_repo.get_db")
async def test_aggregate_project_volume(mock_get_db, mock_db):
    mock_get_db.return_value = mock_db
    res = await aggregate_project_volume()
    assert res == [{"total": 100}]
    mock_db.projects.aggregate.assert_called_once()

@pytest.mark.asyncio
@patch("dashboard_api.repositories.stats_repo.get_db")
async def test_aggregate_conversion_rates(mock_get_db, mock_db):
    mock_get_db.return_value = mock_db
    res = await aggregate_conversion_rates()
    assert res == [{"total": 100}]
    mock_db.projects.aggregate.assert_called_once()

@pytest.mark.asyncio
@patch("dashboard_api.repositories.stats_repo.get_db")
async def test_aggregate_revenue_over_time(mock_get_db, mock_db):
    mock_get_db.return_value = mock_db
    res = await aggregate_revenue_over_time()
    assert res == [{"total": 100}]
    mock_db.projects.aggregate.assert_called_once()

@pytest.mark.asyncio
@patch("dashboard_api.repositories.stats_repo.get_db")
async def test_aggregate_total_revenue(mock_get_db, mock_db):
    mock_get_db.return_value = mock_db
    res = await aggregate_total_revenue()
    assert res == 100
    
    # Test empty result
    mock_db.projects.aggregate.return_value.to_list.return_value = []
    res = await aggregate_total_revenue()
    assert res == 0.0
