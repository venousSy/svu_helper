from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class ProjectResponse(BaseModel):
    id: int
    user_id: int
    username: Optional[str] = None
    user_full_name: Optional[str] = None
    subject_name: str
    tutor_name: str
    deadline: str
    status: str
    price: Optional[int] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class PaginatedProjectsResponse(BaseModel):
    items: List[ProjectResponse]
    total: int
    page: int
    size: int
    pages: int

class OfferRequest(BaseModel):
    price: int
    delivery: str
    notes: Optional[str] = ""

class ActionResponse(BaseModel):
    detail: str
