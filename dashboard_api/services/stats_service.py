import asyncio
from typing import Dict, Any

from dashboard_api.repositories import stats_repo

async def get_overview_stats(start_date: str = None, end_date: str = None) -> Dict[str, Any]:
    """
    Fetches volume, conversion, revenue, and referrers concurrently from the repository.
    """
    volume_task = stats_repo.aggregate_project_volume(start_date, end_date)
    conversion_task = stats_repo.aggregate_conversion_rates(start_date, end_date)
    revenue_task = stats_repo.aggregate_revenue_over_time(start_date, end_date)
    referrers_task = stats_repo.aggregate_top_referrers()
    
    volume, conversion, revenue, referrers = await asyncio.gather(
        volume_task,
        conversion_task,
        revenue_task,
        referrers_task
    )
    
    return {
        "project_volume": volume,
        "conversion_rates": conversion,
        "revenue": revenue,
        "top_referrers": referrers
    }
