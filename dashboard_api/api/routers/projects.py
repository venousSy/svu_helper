import structlog
from typing import Optional
from fastapi import APIRouter, Depends, Query, BackgroundTasks, HTTPException

from dashboard_api.api.dependencies import get_current_user
from dashboard_api.schemas.projects import PaginatedProjectsResponse, OfferRequest, ActionResponse, ProjectDetailsResponse
from dashboard_api.services.projects_service import get_projects_page, get_project_details

from application.offer_service import SendOfferService, FinishProjectService, DenyProjectService
from dashboard_api.services.telegram_service import TelegramService
from application.audit_service import AuditService
from domain.enums import AuditEventType
from infrastructure.mongo_db import get_db
from infrastructure.repositories import ProjectRepository, AuditRepository, PaymentRepository

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

@router.get("/{proj_id}", response_model=ProjectDetailsResponse)
async def get_project(
    proj_id: int,
):
    """
    Returns full details of a specific project, including payment info.
    Requires authentication.
    """
    logger.info("Fetching project details", proj_id=proj_id)
    db = await get_db()
    project_repo = ProjectRepository(db)
    payment_repo = PaymentRepository(db)
    
    return await get_project_details(project_repo, payment_repo, proj_id)

@router.post("/{proj_id}/offer", response_model=ActionResponse)
async def send_offer(
    proj_id: int,
    request: OfferRequest,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(get_current_user)
):
    """Sends an offer to the student and updates the project status."""
    db = await get_db()
    project_repo = ProjectRepository(db)
    audit_repo = AuditRepository(db)
    telegram_service = TelegramService()
    
    try:
        service = SendOfferService(project_repo)
        result = await service.execute(
            proj_id=proj_id,
            price=str(request.price),
            delivery=request.delivery,
            notes=request.notes or ""
        )
    except Exception as e:
        logger.error("Error sending offer", proj_id=proj_id, error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
        
    dashboard_username = current_user
    
    background_tasks.add_task(
        telegram_service.send_offer_notification,
        user_id=result.user_id,
        proj_id=result.proj_id,
        subject=result.subject,
        price=result.price,
        delivery=result.delivery,
        notes=result.notes
    )
    
    background_tasks.add_task(
        AuditService(audit_repo).log_event,
        user_id=0,
        role="dashboard_admin",
        event_type=AuditEventType.OFFER_SENT,
        entity_id=proj_id,
        metadata={"dashboard_user": dashboard_username}
    )
    
    background_tasks.add_task(
        AuditService(audit_repo).log_event,
        user_id=0,
        role="dashboard_admin",
        event_type=AuditEventType.PROJECT_STATUS_CHANGED,
        entity_id=proj_id,
        metadata={"new_status": "offered", "dashboard_user": dashboard_username}
    )
    
    return ActionResponse(detail="Offer sent successfully")

@router.post("/{proj_id}/deny", response_model=ActionResponse)
async def deny_project(
    proj_id: int,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(get_current_user)
):
    """Denies a project from the admin side."""
    db = await get_db()
    project_repo = ProjectRepository(db)
    audit_repo = AuditRepository(db)
    telegram_service = TelegramService()
    
    try:
        service = DenyProjectService(project_repo)
        result = await service.execute_admin_deny(proj_id)
    except Exception as e:
        logger.error("Error denying project", proj_id=proj_id, error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
        
    dashboard_username = current_user
    
    if result.student_user_id:
        background_tasks.add_task(
            telegram_service.send_project_denied,
            user_id=result.student_user_id,
            proj_id=proj_id
        )
        
    background_tasks.add_task(
        AuditService(audit_repo).log_event,
        user_id=0,
        role="dashboard_admin",
        event_type=AuditEventType.PROJECT_STATUS_CHANGED,
        entity_id=proj_id,
        metadata={"new_status": "denied", "dashboard_user": dashboard_username}
    )
    
    return ActionResponse(detail="Project denied successfully")

@router.post("/{proj_id}/finish", response_model=ActionResponse)
async def finish_project(
    proj_id: int,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(get_current_user)
):
    """Marks a project as finished."""
    db = await get_db()
    project_repo = ProjectRepository(db)
    audit_repo = AuditRepository(db)
    telegram_service = TelegramService()
    
    try:
        service = FinishProjectService(project_repo)
        result = await service.execute(proj_id)
    except Exception as e:
        logger.error("Error finishing project", proj_id=proj_id, error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
        
    dashboard_username = current_user
    
    background_tasks.add_task(
        telegram_service.send_project_finished,
        user_id=result.user_id,
        proj_id=result.proj_id,
        subject=result.subject
    )
    
    background_tasks.add_task(
        AuditService(audit_repo).log_event,
        user_id=0,
        role="dashboard_admin",
        event_type=AuditEventType.PROJECT_STATUS_CHANGED,
        entity_id=proj_id,
        metadata={"new_status": "finished", "dashboard_user": dashboard_username}
    )
    
    return ActionResponse(detail="Project marked as finished")
