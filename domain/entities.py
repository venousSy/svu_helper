"""
Domain Entities
===============
Pydantic models representing the core domain objects.
No framework (aiogram) or database (motor) dependencies here.
"""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from domain.enums import PaymentStatus, ProjectStatus


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
    file_type: Optional[str] = None
    status: ProjectStatus = Field(default=ProjectStatus.PENDING)
    price: Optional[str] = None
    delivery_date: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True)


class Payment(BaseModel):
    id: int
    project_id: int
    user_id: int
    file_id: str
    status: PaymentStatus = Field(default=PaymentStatus.PENDING)

    model_config = ConfigDict(use_enum_values=True)
