from typing import Optional, Any, Dict
import math
import structlog

from dashboard_api.repositories.projects_repo import count_projects, get_paginated_projects
from dashboard_api.schemas.projects import PaginatedProjectsResponse, ProjectResponse, ProjectDetailsResponse, PaymentResponse
from typing import List
from infrastructure.repositories.project import ProjectRepository
from infrastructure.repositories.payment import PaymentRepository
from fastapi import HTTPException

logger = structlog.get_logger(__name__)


def _safe_price(value: Any) -> Optional[int]:
    """Coerce price to int — handles string ('150'), float, None, or missing."""
    if value is None:
        return None
    try:
        return int(float(str(value)))
    except (ValueError, TypeError):
        return None


def _to_project_response(doc: Dict[str, Any]) -> Optional[ProjectResponse]:
    """Convert a raw MongoDB document to a ProjectResponse, skipping _id."""
    try:
        clean = {k: v for k, v in doc.items() if k != "_id"}
        clean["price"] = _safe_price(clean.get("price"))
        return ProjectResponse(**clean)
    except Exception as exc:
        logger.warning("Skipping malformed project document", error=str(exc), doc_id=doc.get("id"))
        return None


async def get_projects_page(
    page: int,
    size: int,
    status_filter: Optional[str] = None,
    search_student_id: Optional[int] = None,
) -> PaginatedProjectsResponse:
    skip = (page - 1) * size

    total = await count_projects(status_filter, search_student_id)
    items_raw = await get_paginated_projects(skip, size, status_filter, search_student_id)

    items = [r for doc in items_raw if (r := _to_project_response(doc)) is not None]
    pages = math.ceil(total / size) if size > 0 else 0

    return PaginatedProjectsResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages,
    )

async def get_project_details(
    project_repo: ProjectRepository,
    payment_repo: PaymentRepository,
    proj_id: int
) -> ProjectDetailsResponse:
    doc = await project_repo.get_project_by_id(proj_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Project not found")

    clean = {k: v for k, v in doc.items() if k != "_id"}
    clean["price"] = _safe_price(clean.get("price"))
    
    payment_doc = await payment_repo.get_payment_by_project_id(proj_id)
    payment_response = None
    if payment_doc:
        payment_clean = {k: v for k, v in payment_doc.items() if k != "_id"}
        payment_response = PaymentResponse(**payment_clean)
        
    clean["payment"] = payment_response
    return ProjectDetailsResponse(**clean)

async def get_urgent_projects_list(project_repo: ProjectRepository) -> List[ProjectResponse]:
    items_raw = await project_repo.get_urgent_projects()
    items = [r for doc in items_raw if (r := _to_project_response(doc)) is not None]
    return items
