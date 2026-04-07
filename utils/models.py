"""
Backward-compatibility shim.
The canonical source of truth is now domain.entities.
All code should migrate to: from domain.entities import Project, Payment
"""
from domain.entities import Project, Payment  # noqa: F401

__all__ = ["Project", "Payment"]
