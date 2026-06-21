"""
Unit tests for Peer-Link Module (PeerService).
"""
import pytest
from unittest.mock import AsyncMock, patch
from application.peer_service import PeerService
from domain.enums import AdStatus, MatchStatus

@pytest.fixture
def student_repo():
    return AsyncMock()

@pytest.fixture
def ad_repo():
    return AsyncMock()

@pytest.fixture
def match_repo():
    return AsyncMock()

@pytest.fixture
def catalog_repo():
    return AsyncMock()

@pytest.fixture
def peer_service(student_repo, ad_repo, match_repo, catalog_repo):
    return PeerService(student_repo, ad_repo, match_repo, catalog_repo)

@pytest.mark.asyncio
async def test_update_student_profile(peer_service, student_repo, catalog_repo):
    profile = await peer_service.update_student_profile(
        user_id=1,
        program="CS",
        current_semester="Fall 2025",
        enrolled_courses=["cs101", "math200"]
    )
    assert profile.user_id == 1
    assert profile.program == "CS"
    assert profile.current_semester == "Fall 2025"
    assert profile.enrolled_courses == ["CS101", "MATH200"]
    
    student_repo.upsert_profile.assert_called_once()
    assert catalog_repo.upsert_course.call_count == 2

@pytest.mark.asyncio
async def test_create_project_ad_enforces_limit(peer_service, ad_repo):
    ad_repo.get_active_ads_count_for_user.return_value = 2
    with pytest.raises(ValueError, match="MAX_ADS_REACHED"):
        await peer_service.create_project_ad(
            author_user_id=1,
            course_code="CS101",
            requirements_text="Need partner",
            duration_hours=24
        )

@pytest.mark.asyncio
async def test_create_project_ad_clamps_duration(peer_service, ad_repo, catalog_repo):
    ad_repo.get_active_ads_count_for_user.return_value = 0
    with patch("application.peer_service.uuid.uuid4") as mock_uuid:
        mock_uuid.return_value.hex = "test_ad_id"
        ad = await peer_service.create_project_ad(
            author_user_id=1,
            course_code="cs101",
            requirements_text="Need partner",
            duration_hours=100  # Will be clamped to 36
        )
    
    assert ad.ad_id == "test_ad_id"
    assert ad.course_code == "CS101"
    # Expires at should be ~36 hours from now
    diff = ad.expires_at - ad.created_at
    assert round(diff.total_seconds()) == 36 * 3600
    ad_repo.create_ad.assert_called_once()
    catalog_repo.upsert_course.assert_called_once()

@pytest.mark.asyncio
async def test_send_match_request_validates_active(peer_service, ad_repo):
    mock_ad = AsyncMock()
    mock_ad.status = AdStatus.EXPIRED
    ad_repo.get_ad.return_value = mock_ad
    
    with pytest.raises(ValueError, match="AD_NOT_ACTIVE"):
        await peer_service.send_match_request(requester_user_id=2, ad_id="ad1")

@pytest.mark.asyncio
async def test_send_match_request_success(peer_service, ad_repo, match_repo):
    mock_ad = AsyncMock()
    mock_ad.status = AdStatus.ACTIVE
    mock_ad.author_user_id = 1
    ad_repo.get_ad.return_value = mock_ad
    match_repo.has_pending_request.return_value = False
    
    with patch("application.peer_service.uuid.uuid4") as mock_uuid:
        mock_uuid.return_value.hex = "req1"
        request = await peer_service.send_match_request(requester_user_id=2, ad_id="ad1")
        
    assert request.request_id == "req1"
    assert request.ad_id == "ad1"
    assert request.requester_user_id == 2
    assert request.owner_user_id == 1
    match_repo.create_request.assert_called_once()
