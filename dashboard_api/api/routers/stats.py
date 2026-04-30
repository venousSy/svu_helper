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
async def get_stats_overview():
    """
    Returns aggregated stats for the dashboard overview.
    Requires authentication.
    """
    logger.info("Fetching stats overview")
    return await get_overview_stats()
