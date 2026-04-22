"""
Application Services – Admin Offer & Work Lifecycle
=====================================================
Services covering the admin side of a project's lifecycle:
fetching project details for review, sending an offer to the student,
finishing a project (delivering work), and denying a project.

Services here:
  GetProjectDetailService – fetch full project data for admin review
  SendOfferService        – persist offer and return notification payload
  FinishProjectService    – mark project Finished, return notification payload
  DenyProjectService      – deny from admin or student side, return notify payload
"""
from dataclasses import dataclass
from typing import Optional

from domain.enums import ProjectStatus
from infrastructure.repositories import ProjectRepository
from utils.constants import MSG_PERMISSION_DENIED


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class ProjectDetail:
    """All fields needed to render the admin project-detail message."""
    proj_id: int
    subject: str          # raw (not escaped)
    tutor: str            # raw
    deadline: str         # raw
    details: str          # raw
    file_id: Optional[str]
    file_type: Optional[str]
    user_id: int
    user_full_name: str   # raw
    username: Optional[str]  # raw, may be None


@dataclass
class SendOfferResult:
    """Data the handler needs to notify the student of a new offer."""
    user_id: int
    proj_id: int
    subject: str    # raw
    price: str      # raw
    delivery: str   # raw
    notes: str      # raw


@dataclass
class FinishProjectResult:
    """Data the handler needs to relay finished work to the student."""
    user_id: int
    proj_id: int
    subject: str    # raw


@dataclass
class DenyResult:
    """
    Outcome of a denial action.

    is_admin_deny=True  → admin denied; handler notifies student_user_id.
    is_admin_deny=False → student denied; handler notifies all admin_ids.
    """
    proj_id: int
    is_admin_deny: bool
    student_user_id: Optional[int]  # set only when is_admin_deny=True


# ---------------------------------------------------------------------------
# GetProjectDetailService
# ---------------------------------------------------------------------------

class GetProjectDetailService:
    """Fetches a full project record for the admin detail view."""

    def __init__(self, project_repo: ProjectRepository) -> None:
        self._repo = project_repo

    async def execute(self, proj_id: int) -> Optional[ProjectDetail]:
        project = await self._repo.get_project_by_id(proj_id)
        if not project:
            return None
        return ProjectDetail(
            proj_id=project["id"],
            subject=project["subject_name"],
            tutor=project["tutor_name"],
            deadline=project["deadline"],
            details=project["details"],
            file_id=project.get("file_id"),
            file_type=project.get("file_type"),
            user_id=project["user_id"],
            user_full_name=project.get("user_full_name") or "Unknown",
            username=project.get("username"),
        )


# ---------------------------------------------------------------------------
# SendOfferService
# ---------------------------------------------------------------------------

class SendOfferService:
    """
    Persists price, delivery date, and status=OFFERED.
    Returns the notification payload for the student.

    Raises:
        ValueError: if project not found.
    """

    def __init__(self, project_repo: ProjectRepository) -> None:
        self._repo = project_repo

    async def execute(
        self, proj_id: int, price: str, delivery: str, notes: str
    ) -> SendOfferResult:
        project = await self._repo.get_project_by_id(proj_id)
        if not project:
            raise ValueError(f"Project #{proj_id} not found.")

        await self._repo.update_offer(proj_id, price, delivery)
        await self._repo.update_status(proj_id, ProjectStatus.OFFERED)

        return SendOfferResult(
            user_id=project["user_id"],
            proj_id=proj_id,
            subject=project["subject_name"],
            price=price,
            delivery=delivery,
            notes=notes,
        )


# ---------------------------------------------------------------------------
# FinishProjectService
# ---------------------------------------------------------------------------

class FinishProjectService:
    """
    Marks a project as FINISHED.
    Returns the data the handler needs to relay the work file to the student.

    Raises:
        ValueError: if project not found.
    """

    def __init__(self, project_repo: ProjectRepository) -> None:
        self._repo = project_repo

    async def execute(self, proj_id: int) -> FinishProjectResult:
        project = await self._repo.get_project_by_id(proj_id)
        if not project:
            raise ValueError(f"Project #{proj_id} not found.")

        await self._repo.update_status(proj_id, ProjectStatus.FINISHED)

        return FinishProjectResult(
            user_id=project["user_id"],
            proj_id=proj_id,
            subject=project["subject_name"],
        )


# ---------------------------------------------------------------------------
# DenyProjectService
# ---------------------------------------------------------------------------

class DenyProjectService:
    """
    Handles project denial from either the admin or the student side.

    execute_admin_deny  → updates status to DENIED_ADMIN, notifies student.
    execute_student_deny → validates ownership, updates status to DENIED_STUDENT,
                           notifies admin(s).

    Raises:
        PermissionError: (student deny) if project isn't owned by user.
    """

    def __init__(self, project_repo: ProjectRepository) -> None:
        self._repo = project_repo

    async def execute_admin_deny(self, proj_id: int) -> DenyResult:
        await self._repo.update_status(proj_id, ProjectStatus.DENIED_ADMIN)
        project = await self._repo.get_project_by_id(proj_id)
        return DenyResult(
            proj_id=proj_id,
            is_admin_deny=True,
            student_user_id=project["user_id"] if project else None,
        )

    async def execute_student_deny(self, proj_id: int, user_id: int) -> DenyResult:
        project = await self._repo.get_project_by_id(proj_id)
        if not project or project["user_id"] != user_id:
            raise PermissionError(MSG_PERMISSION_DENIED)
        await self._repo.update_status(proj_id, ProjectStatus.DENIED_STUDENT)
        return DenyResult(
            proj_id=proj_id,
            is_admin_deny=False,
            student_user_id=None,
        )
