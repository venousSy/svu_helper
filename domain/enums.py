"""
Domain Enums
============
Core status value-objects for Project and Payment lifecycles.
These are pure Python – no framework or database dependencies.

IMPORTANT: The string values of ProjectStatus members must exactly match
the values stored in the MongoDB documents (which were originally
sourced from locales/ar.json → utils/constants.py → utils/enums.py).
"""
from enum import Enum


class ProjectStatus(str, Enum):
    PENDING = "قيد المراجعة"
    ACCEPTED = "قيد التنفيذ"
    AWAITING_VERIFICATION = "بانتظار التحقق"
    FINISHED = "منتهى"
    OFFERED = "تم تقديم عرض"
    DENIED_ADMIN = "مرفوض من المشرف"
    DENIED_STUDENT = "ملغى من الطالب"
    REJECTED_PAYMENT = "مرفوض: مشكلة في الدفع"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
