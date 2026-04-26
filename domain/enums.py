"""
Domain Enums
============
Core status value-objects for Project and Payment lifecycles.
These are pure Python – no framework or database dependencies.

IMPORTANT: Enum values are English slugs stored directly in MongoDB.
Display labels (Arabic) live in utils/constants.py -> STATUS_LABELS dict.
Never put display strings here.
"""
from enum import Enum


class ProjectStatus(str, Enum):
    PENDING               = "pending"
    ACCEPTED              = "accepted"
    AWAITING_VERIFICATION = "awaiting_verification"
    FINISHED              = "finished"
    OFFERED               = "offered"
    DENIED_ADMIN          = "denied_admin"
    DENIED_STUDENT        = "denied_student"
    REJECTED_PAYMENT      = "rejected_payment"


class PaymentStatus(str, Enum):
    PENDING  = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class TicketStatus(str, Enum):
    OPEN   = "open"
    CLOSED = "closed"


class AuditEventType(str, Enum):
    PROJECT_CREATED = "project_created"
    PROJECT_STATUS_CHANGED = "project_status_changed"
    OFFER_SENT = "offer_sent"
    OFFER_ACCEPTED = "offer_accepted"
    PAYMENT_SUBMITTED = "payment_submitted"
    PAYMENT_APPROVED = "payment_approved"
    PAYMENT_REJECTED = "payment_rejected"
    TICKET_OPENED = "ticket_opened"
    TICKET_RESOLVED = "ticket_resolved"
