from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any

# Local imports (assuming running from root)
from database import (
    get_all_projects_categorized,
    get_project_by_id,
    update_project_status,
    update_offer_details,
    STATUS_PENDING,
    STATUS_OFFERED,
    STATUS_ACCEPTED,
    STATUS_FINISHED
)
from api.schemas import OfferRequest, ProjectStatus

router = APIRouter()

@router.get("/projects")
async def list_projects():
    """Get all projects categorized by status."""
    return await get_all_projects_categorized()

@router.get("/projects/{project_id}")
async def get_project(project_id: int):
    """Get a single project details."""
    project = await get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.post("/projects/{project_id}/offer")
async def send_offer(project_id: int, offer: OfferRequest):
    """Send an offer to the student (Price + Date)."""
    project = await get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Update DB
    await update_offer_details(project_id, offer.price, offer.delivery_date)
    
    # NOTE: In a real app, we should also trigger the Telegram notification here.
    # For now, we update the DB. We can inject the Bot instance later for notifications.
    
    return {"message": "Offer sent successfully"}

@router.post("/projects/{project_id}/status")
async def change_status(project_id: int, status_update: ProjectStatus):
    """Manually update status."""
    await update_project_status(project_id, status_update.status)
    return {"message": f"Status updated to {status_update.status}"}
