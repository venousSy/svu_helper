import pytest
from unittest.mock import AsyncMock, patch
from dashboard_api.services.stats_service import get_overview_stats

@pytest.mark.asyncio
@patch("dashboard_api.services.stats_service.stats_repo.aggregate_project_volume")
@patch("dashboard_api.services.stats_service.stats_repo.aggregate_conversion_rates")
@patch("dashboard_api.services.stats_service.stats_repo.aggregate_revenue_over_time")
async def test_get_overview_stats(mock_rev, mock_conv, mock_vol):
    mock_vol.return_value = [{"a": 1}]
    mock_conv.return_value = [{"b": 2}]
    mock_rev.return_value = [{"c": 3}]
    
    res = await get_overview_stats()
    assert res["project_volume"] == [{"a": 1}]
    assert res["conversion_rates"] == [{"b": 2}]
    assert res["revenue"] == [{"c": 3}]
