"""
Application Services – Project (Student Flows)
================================================
All use-cases that a student triggers around their project lifecycle.

Services here:
  AddProjectService         – submit a new project (existing)
  VerifyProjectOwnershipService – auth-check before offer acceptance
  GetStudentProjectsService – list all non-offered projects
  GetStudentOffersService   – list OFFERED projects
  GetOfferDetailService     – fetch + validate a single offer detail
"""
from typing import Any, Dict, List, Optional

from domain.entities import _parse_deadline
from domain.enums import ProjectStatus
from infrastructure.repositories import ProjectRepository


# ---------------------------------------------------------------------------
# AddProjectService (original)
# ---------------------------------------------------------------------------

class AddProjectService:
    """Use-case: submit a new project on behalf of a student."""

    MAX_SUBJECT_LENGTH = 150
    MAX_TUTOR_LENGTH = 150
    MAX_DEADLINE_LENGTH = 50
    MAX_DETAILS_LENGTH = 3000
    MAX_FILE_SIZE_MB = 15
    MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

    def __init__(self, project_repo: ProjectRepository) -> None:
        self._repo = project_repo

    async def execute(
        self,
        *,
        user_id: int,
        username: Optional[str],
        user_full_name: str,
        subject: str,
        tutor: str,
        deadline: str,
        details: str,
        file_id: Optional[str],
        file_type: Optional[str],
    ) -> int:
        """Validates inputs and persists the project. Returns the new project ID."""
        self._validate(subject, tutor, deadline, details)
        return await self._repo.add_project(
            user_id=user_id,
            username=username,
            user_full_name=user_full_name,
            subject=subject,
            tutor=tutor,
            deadline=deadline,
            details=details,
            file_id=file_id,
            file_type=file_type,
        )

    def _validate(self, subject: str, tutor: str, deadline: str, details: str) -> None:
        if len(subject) > self.MAX_SUBJECT_LENGTH:
            raise ValueError(f"Subject too long: max {self.MAX_SUBJECT_LENGTH} chars.")
        if len(tutor) > self.MAX_TUTOR_LENGTH:
            raise ValueError(f"Tutor name too long: max {self.MAX_TUTOR_LENGTH} chars.")
        _parse_deadline(deadline)  # raises ValueError with Arabic message on bad format
        if len(details) > self.MAX_DETAILS_LENGTH:
            raise ValueError(f"Details too long: max {self.MAX_DETAILS_LENGTH} chars.")


# ---------------------------------------------------------------------------
# VerifyProjectOwnershipService
# ---------------------------------------------------------------------------

class VerifyProjectOwnershipService:
    """
    Confirms that a project exists and belongs to the requesting user.

    Raises:
        PermissionError: if not found or user_id doesn't match.
    """

    def __init__(self, project_repo: ProjectRepository) -> None:
        self._repo = project_repo

    async def execute(self, proj_id: int, user_id: int) -> Dict[str, Any]:
        project = await self._repo.get_project_by_id(proj_id)
        if not project or project["user_id"] != user_id:
            raise PermissionError("غير مصرح لك بذلك")
        return project


# ---------------------------------------------------------------------------
# GetStudentProjectsService
# ---------------------------------------------------------------------------

# All statuses shown in "My Projects" (excludes OFFERED which has its own menu)
_ALL_PROJECT_STATUSES: List[ProjectStatus] = [
    ProjectStatus.PENDING,
    ProjectStatus.ACCEPTED,
    ProjectStatus.AWAITING_VERIFICATION,
    ProjectStatus.FINISHED,
    ProjectStatus.DENIED_ADMIN,
    ProjectStatus.DENIED_STUDENT,
    ProjectStatus.REJECTED_PAYMENT,
]


class GetStudentProjectsService:
    """Returns all non-offered projects owned by a student."""

    def __init__(self, project_repo: ProjectRepository) -> None:
        self._repo = project_repo

    async def execute(self, user_id: int) -> List[Dict[str, Any]]:
        return await self._repo.get_projects_by_status(
            _ALL_PROJECT_STATUSES, user_id=user_id
        )


# ---------------------------------------------------------------------------
# GetStudentOffersService
# ---------------------------------------------------------------------------

class GetStudentOffersService:
    """Returns projects in OFFERED state for a student."""

    def __init__(self, project_repo: ProjectRepository) -> None:
        self._repo = project_repo

    async def execute(self, user_id: int) -> List[Dict[str, Any]]:
        return await self._repo.get_projects_by_status(
            [ProjectStatus.OFFERED], user_id=user_id
        )


# ---------------------------------------------------------------------------
# GetOfferDetailService
# ---------------------------------------------------------------------------

class GetOfferDetailService:
    """
    Fetches a specific project, validates the requester owns it.

    Raises:
        PermissionError: if not found or user_id doesn't match.
    """

    def __init__(self, project_repo: ProjectRepository) -> None:
        self._repo = project_repo

    async def execute(self, proj_id: int, user_id: int) -> Dict[str, Any]:
        project = await self._repo.get_project_by_id(proj_id)
        if not project or project["user_id"] != user_id:
            raise PermissionError("غير مصرح لك بذلك")
        return project
