import structlog
from fastapi import APIRouter, Depends

from dashboard_api.api.dependencies import get_current_user
from dashboard_api.repositories.referrals_repo import (
    get_referral_tree,
    get_referral_summary,
)

logger = structlog.get_logger(__name__)

router = APIRouter(
    prefix="/api/referrals",
    tags=["referrals"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/summary")
async def referrals_summary():
    """Top-level referral counts and total commissions paid."""
    logger.info("Fetching referral summary")
    return await get_referral_summary()


@router.get("/tree")
async def referrals_tree():
    """
    Full referral tree: each referrer with the users they referred
    and the commission logs per referral.
    """
    logger.info("Fetching referral tree")
    return await get_referral_tree()
