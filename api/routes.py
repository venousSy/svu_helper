from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any

from database.repositories import ProjectRepository
from utils.enums import ProjectStatus
from api.schemas import OfferRequest, ProjectStatus as ApiProjectStatus
from bson import ObjectId

router = APIRouter()

def serialize_mongo(obj):
    """Recursively convert ObjectId to str."""
    if isinstance(obj, list):
        return [serialize_mongo(i) for i in obj]
    if isinstance(obj, dict):
        return {k: serialize_mongo(v) for k, v in obj.items()}
    if isinstance(obj, ObjectId):
        return str(obj)
    return obj

@router.get("/projects")
async def list_projects():
    """Get all projects categorized by status."""
    data = await ProjectRepository.get_all_categorized()
    return serialize_mongo(data)

@router.get("/projects/{project_id}")
async def get_project(project_id: int):
    """Get a single project details."""
    project = await ProjectRepository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return serialize_mongo(project)

@router.post("/projects/{project_id}/offer")
async def send_offer(project_id: int, offer: OfferRequest):
    """Send an offer to the student (Price + Date)."""
    project = await ProjectRepository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Update DB
    await ProjectRepository.update_offer(project_id, offer.price, offer.delivery_date)
    await ProjectRepository.update_status(project_id, ProjectStatus.OFFERED)
    
    return {"message": "Offer sent successfully"}

@router.post("/projects/{project_id}/status")
async def change_status(project_id: int, status_update: ApiProjectStatus):
    """Manually update status."""
    await ProjectRepository.update_status(project_id, status_update.status)
    return {"message": f"Status updated to {status_update.status}"}
