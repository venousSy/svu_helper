import uuid
import structlog
from typing import List, Optional, Tuple
from datetime import datetime, timezone, timedelta

from domain.peer_entities import StudentProfile, ProjectAd, MatchRequest, CourseCatalog
from domain.enums import AdStatus, MatchStatus
from infrastructure.repositories.peer_repo import (
    StudentProfileRepository,
    ProjectAdRepository,
    MatchRequestRepository,
    CourseCatalogRepository
)

logger = structlog.get_logger(__name__)

class PeerService:
    def __init__(
        self,
        student_repo: StudentProfileRepository,
        ad_repo: ProjectAdRepository,
        match_repo: MatchRequestRepository,
        catalog_repo: CourseCatalogRepository
    ):
        self._student_repo = student_repo
        self._ad_repo = ad_repo
        self._match_repo = match_repo
        self._catalog_repo = catalog_repo

    async def update_student_profile(
        self, user_id: int, program: str, current_semester: str, enrolled_courses: List[str]
    ) -> StudentProfile:
        profile = StudentProfile(
            user_id=user_id,
            program=program,
            current_semester=current_semester,
            enrolled_courses=[c.upper() for c in enrolled_courses]
        )
        await self._student_repo.upsert_profile(profile)
        
        # Track unique course codes
        for course in enrolled_courses:
            await self._catalog_repo.upsert_course(CourseCatalog(course_code=course))
            
        logger.info("updated_student_profile", user_id=user_id, courses_count=len(enrolled_courses))
        return profile

    async def get_student_profile(self, user_id: int) -> Optional[StudentProfile]:
        return await self._student_repo.get_profile(user_id)

    async def create_project_ad(
        self, author_user_id: int, course_code: str, requirements_text: str, duration_hours: int
    ) -> ProjectAd:
        """
        Creates a new transient project ad.
        Enforces a maximum of 2 active ads globally per user.
        Limits expiration to 36 hours.
        """
        active_count = await self._ad_repo.get_active_ads_count_for_user(author_user_id)
        if active_count >= 2:
            raise ValueError("MAX_ADS_REACHED")
            
        # Enforce max 36 hours
        duration_hours = min(max(1, duration_hours), 36)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=duration_hours)
        
        ad = ProjectAd(
            ad_id=uuid.uuid4().hex,
            author_user_id=author_user_id,
            course_code=course_code.upper(),
            requirements_text=requirements_text,
            expires_at=expires_at
        )
        await self._ad_repo.create_ad(ad)
        
        # Track in catalog
        await self._catalog_repo.upsert_course(CourseCatalog(course_code=course_code))
        
        logger.info("created_project_ad", ad_id=ad.ad_id, user_id=author_user_id, course=ad.course_code)
        return ad

    async def search_active_ads(self, course_code: str, skip_user_id: int) -> List[ProjectAd]:
        return await self._ad_repo.get_active_ads(course_code, skip_user_id=skip_user_id)

    async def send_match_request(self, requester_user_id: int, ad_id: str) -> MatchRequest:
        ad = await self._ad_repo.get_ad(ad_id)
        if not ad:
            raise ValueError("AD_NOT_FOUND")
            
        if ad.status != AdStatus.ACTIVE:
            raise ValueError("AD_NOT_ACTIVE")
            
        if ad.author_user_id == requester_user_id:
            raise ValueError("CANNOT_REQUEST_OWN_AD")
            
        has_pending = await self._match_repo.has_pending_request(requester_user_id, ad_id)
        if has_pending:
            raise ValueError("REQUEST_ALREADY_PENDING")
            
        request = MatchRequest(
            request_id=uuid.uuid4().hex,
            ad_id=ad_id,
            requester_user_id=requester_user_id,
            owner_user_id=ad.author_user_id
        )
        await self._match_repo.create_request(request)
        
        logger.info("sent_match_request", request_id=request.request_id, from_user=requester_user_id, to_user=ad.author_user_id)
        return request

    async def respond_to_match(self, request_id: str, owner_user_id: int, accept: bool) -> Tuple[bool, Optional[MatchRequest]]:
        """
        Respond to a match request. Returns (success, request).
        If success and accept is True, caller should extract requester_user_id and owner_user_id to share contact info.
        """
        request = await self._match_repo.get_request(request_id)
        if not request:
            return False, None
            
        if request.owner_user_id != owner_user_id:
            return False, None
            
        if request.status != MatchStatus.PENDING:
            return False, None
            
        new_status = MatchStatus.ACCEPTED if accept else MatchStatus.REJECTED
        await self._match_repo.update_request_status(request_id, new_status)
        
        logger.info("responded_to_match", request_id=request_id, owner_user_id=owner_user_id, accept=accept)
        return True, request

    async def expire_old_ads(self) -> int:
        """Background task logic to mark expired ads."""
        count = await self._ad_repo.expire_old_ads()
        if count > 0:
            logger.info("expired_old_ads", count=count)
        return count
