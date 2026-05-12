"""
Domain Entities for Peer-Link Module
====================================
Pydantic models representing the core domain objects for peer discovery and matching.
"""
from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from domain.enums import AdStatus, MatchStatus


class StudentProfile(BaseModel):
    """Represents a student's dynamic academic state."""
    user_id: int
    program: str
    current_semester: str
    enrolled_courses: List[str] = Field(default_factory=list)
    last_updated: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    model_config = ConfigDict(use_enum_values=True)


class ProjectAd(BaseModel):
    """Represents a transient bulletin board post for peer discovery."""
    ad_id: str
    author_user_id: int
    course_code: str
    requirements_text: str
    status: AdStatus = Field(default=AdStatus.ACTIVE)
    expires_at: datetime
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    model_config = ConfigDict(use_enum_values=True)


class MatchRequest(BaseModel):
    """Represents the 'Secure Handshake' between two peers."""
    request_id: str
    ad_id: str
    requester_user_id: int
    owner_user_id: int
    status: MatchStatus = Field(default=MatchStatus.PENDING)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    model_config = ConfigDict(use_enum_values=True)


class CourseCatalog(BaseModel):
    """Stores unique course codes entered by users to build a database over time."""
    course_code: str
    course_name: Optional[str] = None
    first_seen_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    model_config = ConfigDict(use_enum_values=True)
