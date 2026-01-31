from typing import Optional
from pydantic import BaseModel

class OfferRequest(BaseModel):
    price: str
    delivery_date: str
    notes: Optional[str] = None

class ProjectStatus(BaseModel):
    status: str

class LoginRequest(BaseModel):
    password: str
