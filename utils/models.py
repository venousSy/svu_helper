from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from utils.enums import ProjectStatus, PaymentStatus

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
    status: ProjectStatus = Field(default=ProjectStatus.PENDING)
    price: Optional[str] = None
    delivery_date: Optional[str] = None
    
    model_config = ConfigDict(use_enum_values=True)

class Payment(BaseModel):
    id: int
    project_id: int
    user_id: int
    file_id: str
    status: PaymentStatus = Field(default=PaymentStatus.PENDING)  # pending, accepted, rejected
    
    model_config = ConfigDict(use_enum_values=True)
