import structlog
from typing import Optional
from fastapi import APIRouter, Depends, Query

from dashboard_api.api.dependencies import get_current_user
from dashboard_api.services.projects_service import get_projects_page
from dashboard_api.schemas.projects import PaginatedProjectsResponse

logger = structlog.get_logger(__name__)

router = APIRouter(
    prefix="/api/projects",
    tags=["projects"],
    dependencies=[Depends(get_current_user)]
)

@router.get("/", response_model=PaginatedProjectsResponse)
async def list_projects(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    student_id: Optional[int] = Query(None)
):
    """
    Returns a paginated list of projects.
    Requires authentication.
    """
    logger.info("Fetching paginated projects", page=page, size=size, status=status, student_id=student_id)
    return await get_projects_page(page, size, status, student_id)
