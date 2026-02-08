from typing import Optional
from pydantic import BaseModel, Field
from utils.constants import STATUS_PENDING, STATUS_AWAITING_VERIFICATION

class Project(BaseModel):
    id: int
    user_id: int
    username: Optional[str] = None
    user_full_name: Optional[str] = None
    subject_name: str
    tutor_name: str
    deadline: str
    details: str
    file_id: Optional[str] = None
    status: str = Field(default=STATUS_PENDING)
    price: Optional[str] = None
    delivery_date: Optional[str] = None

class Payment(BaseModel):
    id: int
    project_id: int
    user_id: int
    file_id: str
    status: str = Field(default="pending")  # pending, accepted, rejected
