"""
Application Services – Admin reads & system control
=====================================================
Thin services wrapping the admin read-only queries and system control
operations. Each service is its own class so handlers receive exactly
the dependency they need and tests can mock precisely.

Services here:
  GetCategorizedProjectsService – full master report data
  GetPendingProjectsService     – projects awaiting review
  GetOngoingProjectsService     – accepted + awaiting-verification projects
  GetProjectHistoryService      – finished / denied projects
  GetAllPaymentsService         – all payment records (for history view)
  GetStatsService               – aggregate statistics
  MaintenanceService            – enable / disable maintenance mode
  GetAllUserIdsService          – user-id list for broadcast
"""
from typing import Any, Dict, List

from domain.enums import ProjectStatus
from infrastructure.repositories import (
    PaymentRepository,
    ProjectRepository,
    SettingsRepository,
    StatsRepository,
)


class GetCategorizedProjectsService:
    """Returns all projects grouped into display categories."""

    def __init__(self, project_repo: ProjectRepository) -> None:
        self._repo = project_repo

    async def execute(self) -> Dict[str, List[Dict[str, Any]]]:
        return await self._repo.get_all_categorized()


class GetPendingProjectsService:
    """Returns all projects awaiting admin review."""

    def __init__(self, project_repo: ProjectRepository) -> None:
        self._repo = project_repo

    async def execute(self) -> List[Dict[str, Any]]:
        return await self._repo.get_projects_by_status([ProjectStatus.PENDING])


class GetOngoingProjectsService:
    """Returns accepted and awaiting-verification (in-progress) projects."""

    def __init__(self, project_repo: ProjectRepository) -> None:
        self._repo = project_repo

    async def execute(self) -> List[Dict[str, Any]]:
        return await self._repo.get_projects_by_status(
            [ProjectStatus.ACCEPTED, ProjectStatus.AWAITING_VERIFICATION]
        )


class GetProjectHistoryService:
    """Returns finished and denied projects for the history view."""

    def __init__(self, project_repo: ProjectRepository) -> None:
        self._repo = project_repo

    async def execute(self) -> List[Dict[str, Any]]:
        return await self._repo.get_projects_by_status(
            [
                ProjectStatus.FINISHED,
                ProjectStatus.DENIED_ADMIN,
                ProjectStatus.DENIED_STUDENT,
                ProjectStatus.REJECTED_PAYMENT,
            ]
        )


class GetAllPaymentsService:
    """Returns all payment records sorted by ID descending."""

    def __init__(self, payment_repo: PaymentRepository) -> None:
        self._repo = payment_repo

    async def execute(self) -> List[Dict[str, Any]]:
        return await self._repo.get_all()


class GetStatsService:
    """Returns the aggregate project statistics dict."""

    def __init__(self, stats_repo: StatsRepository) -> None:
        self._repo = stats_repo

    async def execute(self) -> Dict[str, int]:
        return await self._repo.get_stats()


class MaintenanceService:
    """Enables or disables global maintenance mode."""

    def __init__(self, settings_repo: SettingsRepository) -> None:
        self._repo = settings_repo

    async def enable(self) -> None:
        await self._repo.set_maintenance_mode(True)

    async def disable(self) -> None:
        await self._repo.set_maintenance_mode(False)


class GetAllUserIdsService:
    """Returns the list of all distinct user IDs (used by broadcast)."""

    def __init__(self, project_repo: ProjectRepository) -> None:
        self._repo = project_repo

    async def execute(self) -> List[int]:
        return await self._repo.get_all_user_ids()
