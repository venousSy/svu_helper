import asyncio
from typing import Dict, Any

from dashboard_api.repositories import stats_repo

async def get_overview_stats() -> Dict[str, Any]:
    """
    Fetches volume, conversion, and revenue concurrently from the repository.
    """
    volume_task = stats_repo.aggregate_project_volume()
    conversion_task = stats_repo.aggregate_conversion_rates()
    revenue_task = stats_repo.aggregate_revenue_over_time()
    
    volume, conversion, revenue = await asyncio.gather(
        volume_task,
        conversion_task,
        revenue_task
    )
    
    return {
        "project_volume": volume,
        "conversion_rates": conversion,
        "revenue": revenue
    }
