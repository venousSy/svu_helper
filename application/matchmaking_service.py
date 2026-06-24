"""
Application Services – Team Matchmaking
========================================
Business logic for team formation: creating requests, finding teams,
joining, and handling join decisions with automatic quota management.
"""
from typing import Any, Dict, List, Optional

from domain.enums import TeamRequestStatus, MatchStatus
from infrastructure.repositories.matchmaking import TeamRequestRepository


class CreateTeamRequestService:
    """Use-case: host creates a new team request."""

    MAX_COURSE_LENGTH = 50
    ALLOWED_MEMBER_COUNTS = [1, 2, 3]

    def __init__(self, team_request_repo: TeamRequestRepository) -> None:
        self._repo = team_request_repo

    async def execute(
        self,
        *,
        host_id: int,
        host_name: Optional[str],
        host_username: Optional[str],
        course_name: str,
        doctor_name: str,
        specialization: str,
        required_members: int,
    ) -> int:
        """Validates inputs and persists the team request. Returns the new ID."""
        if not course_name or len(course_name) > self.MAX_COURSE_LENGTH:
            raise ValueError("Invalid course name.")
        if required_members not in self.ALLOWED_MEMBER_COUNTS:
            raise ValueError("Required members must be 1, 2, or 3.")
            
        if await self._repo.has_global_open_team_for_subject(course_name, doctor_name):
            raise ValueError("global_team_exists")
            
        if await self._repo.has_active_involvement_for_course(host_id, course_name):
            raise ValueError("active_involvement_exists")
            
        return await self._repo.create_team_request(
            host_id=host_id,
            host_name=host_name,
            host_username=host_username,
            course_name=course_name,
            doctor_name=doctor_name,
            specialization=specialization,
            required_members=required_members,
        )


class FindOpenTeamsService:
    """Use-case: seeker searches for open teams matching their courses."""

    def __init__(self, team_request_repo: TeamRequestRepository) -> None:
        self._repo = team_request_repo

    async def execute(
        self,
        specialization: str,
        seeker_id: int,
    ) -> List[Dict[str, Any]]:
        return await self._repo.get_open_teams_for_specialization(specialization, seeker_id)

    async def get_user_pending_joins(self, seeker_id: int) -> List[Dict[str, Any]]:
        return await self._repo.get_user_pending_joins(seeker_id)


class JoinTeamService:
    """Use-case: seeker requests to join an open team."""

    def __init__(self, team_request_repo: TeamRequestRepository) -> None:
        self._repo = team_request_repo

    async def execute(
        self,
        request_id: int,
        seeker_id: int,
        seeker_name: Optional[str],
    ) -> Dict[str, Any]:
        """
        Validates and adds a join request.

        Returns the team request document.
        Raises ValueError with a message key on validation failure.
        """
        team = await self._repo.get_by_id(request_id)
        if not team:
            raise ValueError("not_found")
        if team["status"] != TeamRequestStatus.OPEN.value:
            raise ValueError("closed")
        if team["host_id"] == seeker_id:
            raise ValueError("own_team")
        if seeker_id in team["current_members"]:
            raise ValueError("already_member")
        if await self._repo.has_join_request(request_id, seeker_id):
            raise ValueError("duplicate")
            
        if await self._repo.has_active_involvement_for_course(seeker_id, team["course_name"]):
            raise ValueError("active_involvement_exists")

        await self._repo.add_join_request(request_id, seeker_id, seeker_name)
        return team


class HandleJoinDecisionService:
    """Use-case: host accepts or rejects a join request."""

    def __init__(self, team_request_repo: TeamRequestRepository) -> None:
        self._repo = team_request_repo

    async def accept(
        self, request_id: int, seeker_id: int
    ) -> Dict[str, Any]:
        """
        Accepts a join request: adds member, checks quota, auto-closes.

        Returns dict with 'team', 'is_full' keys.
        """
        team_check = await self._repo.get_by_id(request_id)
        if len(team_check["current_members"]) >= team_check["required_members"]:
            raise ValueError("team_full")
            
        success = await self._repo.atomic_accept_member(request_id, seeker_id)
        if not success:
            raise ValueError("team_full")

        team = await self._repo.get_by_id(request_id)
        current_count = len(team["current_members"])
        is_full = current_count >= team["required_members"]

        if is_full:
            await self._repo.close_request(request_id)
            await self._repo.reject_all_pending_joins(request_id)

        return {"team": team, "is_full": is_full}

    async def reject(
        self, request_id: int, seeker_id: int
    ) -> Dict[str, Any]:
        """Rejects a join request. Returns the team request document."""
        await self._repo.update_join_request_status(
            request_id, seeker_id, MatchStatus.REJECTED
        )
        return await self._repo.get_by_id(request_id)

class ManageTeamService:
    """Use-case: host manages an open team or seeker manages their join requests."""

    def __init__(self, team_request_repo: TeamRequestRepository) -> None:
        self._repo = team_request_repo

    async def close_team(self, request_id: int, host_id: int) -> None:
        team = await self._repo.get_by_id(request_id)
        if not team or team["host_id"] != host_id:
            raise ValueError("not_authorized")
        await self._repo.close_request(request_id)
        await self._repo.reject_all_pending_joins(request_id)

    async def delete_team(self, request_id: int, host_id: int) -> None:
        team = await self._repo.get_by_id(request_id)
        if not team or team["host_id"] != host_id:
            raise ValueError("not_authorized")
        await self._repo.delete_request(request_id)

    async def withdraw_join(self, request_id: int, seeker_id: int) -> None:
        team = await self._repo.get_by_id(request_id)
        if not team:
            raise ValueError("not_found")
        await self._repo.remove_join_request(request_id, seeker_id)
