"""
Domain Entities
===============
Pydantic models representing the core domain objects.
No framework (aiogram) or database (motor) dependencies here.
"""
import re
from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from domain.enums import PaymentStatus, ProjectStatus, TicketStatus

# Accepted deadline formats: DD/MM/YYYY  or  YYYY-MM-DD (ISO 8601)
_DEADLINE_RE = re.compile(
    r"^(?:"
    r"(?P<dmy>\d{2}/\d{2}/\d{4})"  # DD/MM/YYYY
    r"|"
    r"(?P<iso>\d{4}-\d{2}-\d{2})"  # YYYY-MM-DD
    r")$"
)


def _parse_deadline(value: str) -> str:
    """Validate deadline and normalise to YYYY-MM-DD for DB storage."""
    value = value.strip()
    m = _DEADLINE_RE.match(value)
    if not m:
        raise ValueError(
            "صيغة التاريخ غير صحيحة. استخدم DD/MM/YYYY أو YYYY-MM-DD "
            "(مثال: 31/12/2025 أو 2025-12-31)."
        )
    if m.group("dmy"):
        # Convert DD/MM/YYYY → YYYY-MM-DD for consistent storage
        day, month, year = value.split("/")
        try:
            datetime(int(year), int(month), int(day))
        except ValueError:
            raise ValueError(
                "التاريخ غير صحيح (يوم/شهر/سنة). تأكد من صحة القيم."
            )
        return f"{year}-{month}-{day}"
    # ISO path – verify the calendar date is real
    try:
        datetime.fromisoformat(value)
    except ValueError:
        raise ValueError("التاريخ غير صحيح. تأكد من صحة اليوم والشهر والسنة.")
    return value


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
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    model_config = ConfigDict(use_enum_values=True)

    @field_validator("deadline", mode="before")
    @classmethod
    def validate_deadline(cls, v: str) -> str:  # noqa: N805
        return _parse_deadline(v)


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
    message_thread_id: Optional[int] = None  # Telegram Forum Topic ID
    status: TicketStatus = Field(default=TicketStatus.OPEN)
    messages: List[TicketMessage] = Field(default_factory=list)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    model_config = ConfigDict(use_enum_values=True)
