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

class PaymentResponse(BaseModel):
    id: int
    file_id: str
    file_type: Optional[str] = None
    status: str
    created_at: datetime

class ProjectDetailsResponse(ProjectResponse):
    details: str
    delivery_date: Optional[str] = None
    attachments: List[dict] = []
    payment: Optional[PaymentResponse] = None

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
