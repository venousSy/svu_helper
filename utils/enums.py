"""
Backward-compatibility shim.
The canonical source of truth is now domain.enums.
All code should migrate to: from domain.enums import ProjectStatus, PaymentStatus
"""
from domain.enums import ProjectStatus, PaymentStatus  # noqa: F401

__all__ = ["ProjectStatus", "PaymentStatus"]
