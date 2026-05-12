from typing import List, Optional
from datetime import datetime, timezone
import structlog
from motor.motor_asyncio import AsyncIOMotorDatabase

from domain.peer_entities import StudentProfile, ProjectAd, MatchRequest, CourseCatalog
from domain.enums import AdStatus, MatchStatus

logger = structlog.get_logger(__name__)


class StudentProfileRepository:
    """Repository for student profiles (Academic State)."""
    def __init__(self, db: AsyncIOMotorDatabase):
        self._collection = db.get_collection("student_profiles")

    async def get_profile(self, user_id: int) -> Optional[StudentProfile]:
        doc = await self._collection.find_one({"user_id": user_id})
        return StudentProfile(**doc) if doc else None

    async def upsert_profile(self, profile: StudentProfile) -> None:
        await self._collection.replace_one(
            {"user_id": profile.user_id},
            profile.model_dump(mode="json"),
            upsert=True
        )


class ProjectAdRepository:
    """Repository for transient peer discovery project ads."""
    def __init__(self, db: AsyncIOMotorDatabase):
        self._collection = db.get_collection("project_ads")

    async def create_ad(self, ad: ProjectAd) -> None:
        await self._collection.insert_one(ad.model_dump(mode="json"))

    async def get_active_ads(self, course_code: str, skip_user_id: Optional[int] = None) -> List[ProjectAd]:
        query = {
            "course_code": course_code.upper(),
            "status": AdStatus.ACTIVE.value,
            "expires_at": {"$gt": datetime.now(timezone.utc).isoformat()}
        }
        if skip_user_id:
            query["author_user_id"] = {"$ne": skip_user_id}
            
        cursor = self._collection.find(query).sort("created_at", -1)
        return [ProjectAd(**doc) async for doc in cursor]

    async def get_ad(self, ad_id: str) -> Optional[ProjectAd]:
        doc = await self._collection.find_one({"ad_id": ad_id})
        return ProjectAd(**doc) if doc else None

    async def update_ad_status(self, ad_id: str, status: AdStatus) -> None:
        await self._collection.update_one(
            {"ad_id": ad_id},
            {"$set": {"status": status.value}}
        )

    async def get_active_ads_count_for_user(self, user_id: int) -> int:
        query = {
            "author_user_id": user_id,
            "status": AdStatus.ACTIVE.value,
            "expires_at": {"$gt": datetime.now(timezone.utc).isoformat()}
        }
        return await self._collection.count_documents(query)
        
    async def expire_old_ads(self) -> int:
        """Sets status to EXPIRED for all active ads whose expires_at is in the past."""
        query = {
            "status": AdStatus.ACTIVE.value,
            "expires_at": {"$lte": datetime.now(timezone.utc).isoformat()}
        }
        result = await self._collection.update_many(
            query,
            {"$set": {"status": AdStatus.EXPIRED.value}}
        )
        return result.modified_count


class MatchRequestRepository:
    """Repository for secure handshake match requests."""
    def __init__(self, db: AsyncIOMotorDatabase):
        self._collection = db.get_collection("match_requests")

    async def create_request(self, request: MatchRequest) -> None:
        await self._collection.insert_one(request.model_dump(mode="json"))

    async def get_request(self, request_id: str) -> Optional[MatchRequest]:
        doc = await self._collection.find_one({"request_id": request_id})
        return MatchRequest(**doc) if doc else None

    async def update_request_status(self, request_id: str, status: MatchStatus) -> None:
        await self._collection.update_one(
            {"request_id": request_id},
            {"$set": {"status": status.value}}
        )

    async def has_pending_request(self, requester_user_id: int, ad_id: str) -> bool:
        doc = await self._collection.find_one({
            "requester_user_id": requester_user_id,
            "ad_id": ad_id,
            "status": MatchStatus.PENDING.value
        })
        return bool(doc)


class CourseCatalogRepository:
    """Repository to build a catalog of unique course codes and names over time."""
    def __init__(self, db: AsyncIOMotorDatabase):
        self._collection = db.get_collection("course_catalog")

    async def upsert_course(self, course: CourseCatalog) -> None:
        # We use $setOnInsert so we don't overwrite first_seen_at
        # and $set to update course_name if provided
        update_doc = {
            "$set": {
                "course_code": course.course_code.upper()
            },
            "$setOnInsert": {
                "first_seen_at": course.first_seen_at.isoformat()
            }
        }
        if course.course_name:
            update_doc["$set"]["course_name"] = course.course_name
            
        await self._collection.update_one(
            {"course_code": course.course_code.upper()},
            update_doc,
            upsert=True
        )

    async def get_all_courses(self) -> List[CourseCatalog]:
        cursor = self._collection.find().sort("course_code", 1)
        return [CourseCatalog(**doc) async for doc in cursor]
