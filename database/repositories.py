"""
Backward-compatibility shim.
The canonical DI-enabled repositories live in infrastructure.repositories.
All new code should import from there or receive instances via middleware.
"""
from infrastructure.repositories import (  # noqa: F401
    PaymentRepository,
    ProjectRepository,
    SettingsRepository,
    StatsRepository,
)

__all__ = [
    "ProjectRepository",
    "PaymentRepository",
    "StatsRepository",
    "SettingsRepository",
]
