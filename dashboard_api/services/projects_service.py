from typing import Optional
import math

from dashboard_api.repositories.projects_repo import count_projects, get_paginated_projects
from dashboard_api.schemas.projects import PaginatedProjectsResponse, ProjectResponse

async def get_projects_page(page: int, size: int, status_filter: Optional[str] = None, search_student_id: Optional[int] = None) -> PaginatedProjectsResponse:
    skip = (page - 1) * size
    
    total = await count_projects(status_filter, search_student_id)
    items_raw = await get_paginated_projects(skip, size, status_filter, search_student_id)
    
    # Mongo _id is ignored because our domain entity has 'id'
    items = [ProjectResponse(**item) for item in items_raw]
    pages = math.ceil(total / size) if size > 0 else 0
    
    return PaginatedProjectsResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages
    )
