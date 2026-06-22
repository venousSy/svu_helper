from typing import Any, Dict, List, Optional
import structlog

from domain.entities import TeamRequest, JoinRequest
from domain.enums import TeamRequestStatus, MatchStatus
from infrastructure.mongo_db import Database

logger = structlog.get_logger()


class TeamRequestRepository:
    def __init__(self, db) -> None:
        self._db = db

    async def create_team_request(
        self,
        *,
        host_id: int,
        host_name: Optional[str],
        host_username: Optional[str],
        course_name: str,
        required_members: int,
    ) -> int:
        """Insert a new team request with auto-incremented ID."""
        request_id = await Database.get_next_sequence("team_request_id")
        team_request = TeamRequest(
            id=request_id,
            host_id=host_id,
            host_name=host_name,
            host_username=host_username,
            course_name=course_name,
            required_members=required_members,
        )
        await self._db.team_requests.insert_one(team_request.model_dump())
        logger.info("Team request created", request_id=request_id, host_id=host_id, course=course_name)
        return request_id

    async def get_by_id(self, request_id: int) -> Optional[Dict[str, Any]]:
        """Fetch a single team request by ID."""
        return await self._db.team_requests.find_one({"id": int(request_id)})

    async def get_open_by_courses(
        self,
        course_names: List[str],
        exclude_user_id: int,
    ) -> List[Dict[str, Any]]:
        """Fetch open requests matching given courses, excluding the user's own."""
        cursor = self._db.team_requests.find({
            "status": TeamRequestStatus.OPEN.value,
            "course_name": {"$in": course_names},
            "host_id": {"$ne": exclude_user_id},
        }).sort("created_at", -1)
        return await cursor.to_list(length=100)

    async def add_join_request(
        self,
        request_id: int,
        seeker_id: int,
        seeker_name: Optional[str],
    ) -> None:
        """Push a JoinRequest to the join_requests array."""
        join_req = JoinRequest(
            seeker_id=seeker_id,
            seeker_name=seeker_name,
        )
        await self._db.team_requests.update_one(
            {"id": int(request_id)},
            {"$push": {"join_requests": join_req.model_dump()}},
        )
        logger.info("Join request added", request_id=request_id, seeker_id=seeker_id)

    async def update_join_request_status(
        self,
        request_id: int,
        seeker_id: int,
        status: str,
    ) -> None:
        """Update the status of a specific join request."""
        await self._db.team_requests.update_one(
            {"id": int(request_id), "join_requests.seeker_id": seeker_id},
            {"$set": {"join_requests.$.status": status}},
        )
        logger.info("Join request status updated", request_id=request_id, seeker_id=seeker_id, status=status)

    async def add_member(self, request_id: int, user_id: int) -> None:
        """Push a user to the current_members list."""
        await self._db.team_requests.update_one(
            {"id": int(request_id)},
            {"$addToSet": {"current_members": user_id}},
        )
        logger.info("Member added to team", request_id=request_id, user_id=user_id)

    async def close_request(self, request_id: int) -> None:
        """Set status to CLOSED."""
        await self._db.team_requests.update_one(
            {"id": int(request_id)},
            {"$set": {"status": TeamRequestStatus.CLOSED.value}},
        )
        logger.info("Team request closed", request_id=request_id)

    async def get_user_open_requests(self, user_id: int) -> List[Dict[str, Any]]:
        """Get a host's own open team requests."""
        cursor = self._db.team_requests.find({
            "host_id": user_id,
            "status": TeamRequestStatus.OPEN.value,
        }).sort("created_at", -1)
        return await cursor.to_list(length=50)

    async def has_pending_join(
        self, request_id: int, seeker_id: int
    ) -> bool:
        """Check if a seeker already has a pending join request."""
        doc = await self._db.team_requests.find_one({
            "id": int(request_id),
            "join_requests": {
                "$elemMatch": {
                    "seeker_id": seeker_id,
                    "status": MatchStatus.PENDING,
                }
            },
        })
        return doc is not None
