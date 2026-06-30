import structlog
from fastapi import APIRouter, Depends

from dashboard_api.api.dependencies import get_current_user
from dashboard_api.services.stats_service import get_overview_stats
from dashboard_api.schemas.stats import StatsOverviewResponse

logger = structlog.get_logger(__name__)

router = APIRouter(
    prefix="/api/stats",
    tags=["stats"],
    dependencies=[Depends(get_current_user)]
)

@router.get("/overview", response_model=StatsOverviewResponse)
async def get_stats_overview(
    start_date: str = None,
    end_date: str = None
):
    """
    Returns aggregated stats for the dashboard overview.
    Requires authentication.
    """
    logger.info("Fetching stats overview", start_date=start_date, end_date=end_date)
    return await get_overview_stats(start_date, end_date)
