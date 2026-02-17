
from enum import Enum
from utils.constants import (
    STATUS_PENDING,
    STATUS_ACCEPTED,
    STATUS_AWAITING_VERIFICATION,
    STATUS_FINISHED,
    STATUS_OFFERED,
    STATUS_REJECTED_PAYMENT,
    STATUS_DENIED_ADMIN,
    STATUS_DENIED_STUDENT,
)

class ProjectStatus(str, Enum):
    PENDING = STATUS_PENDING
    ACCEPTED = STATUS_ACCEPTED
    AWAITING_VERIFICATION = STATUS_AWAITING_VERIFICATION
    FINISHED = STATUS_FINISHED
    OFFERED = STATUS_OFFERED
    DENIED_ADMIN = STATUS_DENIED_ADMIN
    DENIED_STUDENT = STATUS_DENIED_STUDENT
    # Adding REJECTED_PAYMENT here might be tricky if it's considered a project status in some flows
    # Based on constants.py, it seems so.
    REJECTED_PAYMENT = STATUS_REJECTED_PAYMENT

class PaymentStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
