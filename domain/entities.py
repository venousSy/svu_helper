"""
Domain Entities
===============
Pydantic models representing the core domain objects.
No framework (aiogram) or database (motor) dependencies here.
"""
import re
from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from domain.enums import (
    PaymentStatus, ProjectStatus, TicketStatus, AuditEventType,
    MatchStatus, TeamRequestStatus,
)
from utils.constants import (
    MSG_INVALID_DATE_FORMAT,
    MSG_INVALID_DATE_VALUES,
    MSG_DATE_IN_PAST
)

# Accepted deadline formats: DD/MM/YYYY  or  YYYY-MM-DD (ISO 8601)
_DEADLINE_RE = re.compile(
    r"^(?:"
    r"(?P<dmy>\d{2}/\d{2}/\d{4})"  # DD/MM/YYYY
    r"|"
    r"(?P<iso>\d{4}-\d{2}-\d{2})"  # YYYY-MM-DD
    r")$"
)


def parse_deadline(value: str) -> str:
    """Validate deadline and normalise to YYYY-MM-DD for DB storage."""
    value = value.strip()
    m = _DEADLINE_RE.match(value)
    if not m:
        raise ValueError(MSG_INVALID_DATE_FORMAT)
    
    parsed_date = None
    if m.group("dmy"):
        # Convert DD/MM/YYYY → YYYY-MM-DD for consistent storage
        day, month, year = value.split("/")
        try:
            parsed_date = datetime(int(year), int(month), int(day)).date()
        except ValueError:
            raise ValueError(MSG_INVALID_DATE_VALUES)
        iso_value = f"{year}-{month}-{day}"
    else:
        # ISO path – verify the calendar date is real
        try:
            parsed_date = datetime.fromisoformat(value).date()
        except ValueError:
            raise ValueError(MSG_INVALID_DATE_VALUES)
        iso_value = value
        
    # Check if date is in the past
    if parsed_date < datetime.now(timezone.utc).date():
        raise ValueError(MSG_DATE_IN_PAST)
        
    return iso_value


class Project(BaseModel):
    id: int
    user_id: int
    username: Optional[str] = None
    user_full_name: Optional[str] = None
    subject_name: str
    tutor_name: str
    deadline: str
    details: str
    attachments: List[dict] = Field(default_factory=list)
    status: ProjectStatus = Field(default=ProjectStatus.PENDING)
    price: Optional[int] = None
    delivery_date: Optional[str] = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    model_config = ConfigDict(use_enum_values=True)

    @field_validator("deadline", mode="before")
    @classmethod
    def validate_deadline(cls, v: str) -> str:  # noqa: N805
        return parse_deadline(v)


class Payment(BaseModel):
    id: int
    project_id: int
    user_id: int
    file_id: str
    file_type: Optional[str] = None   # photo / document / video / etc.
    status: PaymentStatus = Field(default=PaymentStatus.PENDING)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    model_config = ConfigDict(use_enum_values=True)


class TicketMessage(BaseModel):
    """A single message inside a support ticket conversation."""
    sender: str                        # "user" | "admin"
    text: Optional[str] = None
    file_id: Optional[str] = None
    file_type: Optional[str] = None    # photo / document / video / …
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class Ticket(BaseModel):
    """Root document for the tickets collection."""
    ticket_id: int
    user_id: int
    username: Optional[str] = None
    user_full_name: Optional[str] = None
    message_thread_id: Optional[int] = None  # Telegram Forum Topic ID
    status: TicketStatus = Field(default=TicketStatus.OPEN)
    messages: List[TicketMessage] = Field(default_factory=list)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    model_config = ConfigDict(use_enum_values=True)


class AuditLog(BaseModel):
    id: str
    user_id: int
    role: str
    event_type: AuditEventType
    entity_id: int
    metadata: Optional[dict] = Field(default_factory=dict)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    model_config = ConfigDict(use_enum_values=True)


class JoinRequest(BaseModel):
    """A pending/resolved request from a seeker to join a team."""
    seeker_id: int
    seeker_name: Optional[str] = None
    status: MatchStatus = Field(default=MatchStatus.PENDING)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    model_config = ConfigDict(use_enum_values=True)


class StudentProfile(BaseModel):
    """A user profile containing their specialization."""
    user_id: int
    specialization: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    model_config = ConfigDict(use_enum_values=True)


class TeamRequest(BaseModel):
    """A team formation request posted by a host student."""
    id: int
    host_id: int
    host_name: Optional[str] = None
    host_username: Optional[str] = None
    course_name: str
    doctor_name: str
    specialization: str
    required_members: int
    current_members: List[int] = Field(default_factory=list)
    join_requests: List[JoinRequest] = Field(default_factory=list)
    status: TeamRequestStatus = Field(default=TeamRequestStatus.OPEN)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    model_config = ConfigDict(use_enum_values=True)


class ReferralUser(BaseModel):
    """Tracks a bot user's referral chain and ShamCash balance."""
    user_id: int
    referred_by: Optional[int] = None
    balance: float = Field(default=0.0)
    last_withdrawal_date: Optional[str] = None  # ISO date string "YYYY-MM-DD" (UTC)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(use_enum_values=True)


class WithdrawalRequest(BaseModel):
    """A single ShamCash withdrawal request submitted by a user."""
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: int
    amount: float
    shamcash_address: str
    shamcash_name: str
    status: str = "pending"   # "pending" | "processed" | "rejected"
    requested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    # ── Admin processing fields (set when admin acts) ──
    processed_at: Optional[datetime] = None     # timestamp of admin action
    processed_by: Optional[str] = None          # "admin_bot" or dashboard username
    shamcash_ref: Optional[str] = None          # ShamCash transaction reference (optional)


class CommissionLog(BaseModel):
    """Audit record written every time a referral commission is earned."""
    log_id: str = Field(default_factory=lambda: str(uuid4()))
    referrer_id: int          # user who receives the commission
    referred_user_id: int     # the student whose payment triggered it
    project_id: int
    project_subject: str
    project_price: float
    commission_amount: float  # always project_price * 0.10
    earned_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
