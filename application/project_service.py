"""
Application Service – Add Project
===================================
Encapsulates the use-case of submitting a new student project.

This class sits between the handler (infrastructure / UI) and the
repository (infrastructure / DB). It is the *only* place that
should contain the business rules for project creation, making it
independently testable without aiogram or MongoDB.

Usage in a handler:
    service = AddProjectService(project_repo)
    project_id = await service.execute(user_id=..., subject=..., ...)

Usage in a unit test:
    mock_repo = AsyncMock(spec=ProjectRepository)
    service = AddProjectService(mock_repo)
    await service.execute(...)
    mock_repo.add_project.assert_called_once()
"""
from typing import Optional

from domain.entities import _parse_deadline
from infrastructure.repositories import ProjectRepository


class AddProjectService:
    """Use-case: submit a new project on behalf of a student."""

    # Validation limits – single place to change them
    MAX_SUBJECT_LENGTH = 150
    MAX_TUTOR_LENGTH = 150
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
        """
        Validates inputs and persists the project.

        Returns:
            The auto-generated integer project ID.

        Raises:
            ValueError: If any field fails validation.
        """
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

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _validate(
        self, subject: str, tutor: str, deadline: str, details: str
    ) -> None:
        if len(subject) > self.MAX_SUBJECT_LENGTH:
            raise ValueError(
                f"Subject too long: max {self.MAX_SUBJECT_LENGTH} chars."
            )
        if len(tutor) > self.MAX_TUTOR_LENGTH:
            raise ValueError(
                f"Tutor name too long: max {self.MAX_TUTOR_LENGTH} chars."
            )
        # Delegate deadline format validation to the domain entity helper.
        # Raises ValueError with an Arabic error message if format is invalid.
        _parse_deadline(deadline)
        if len(details) > self.MAX_DETAILS_LENGTH:
            raise ValueError(
                f"Details too long: max {self.MAX_DETAILS_LENGTH} chars."
            )
