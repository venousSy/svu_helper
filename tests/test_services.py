"""
Unit tests for new application-layer services.
================================================
Pattern: mock only the repo, test only the service's business rules.
No MongoDB, no aiogram, no network calls.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from application.offer_service import (
    DenyProjectService,
    FinishProjectService,
    GetProjectDetailService,
    ProjectDetail,
    SendOfferService,
)
from application.payment_service import (
    ConfirmPaymentService,
    RejectPaymentService,
    SubmitPaymentService,
)
from application.project_service import (
    AddProjectService,
    GetOfferDetailService,
    GetStudentOffersService,
    GetStudentProjectsService,
    VerifyProjectOwnershipService,
)
from domain.enums import PaymentStatus, ProjectStatus


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_project_repo():
    return AsyncMock()

@pytest.fixture
def mock_payment_repo():
    return AsyncMock()

@pytest.fixture
def mock_stats_repo():
    return AsyncMock()


# ---------------------------------------------------------------------------
# AddProjectService
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_add_project_service_validates_subject_length(mock_project_repo):
    service = AddProjectService(mock_project_repo)
    with pytest.raises(ValueError, match="Subject too long"):
        await service.execute(
            user_id=1, username="u", user_full_name="U",
            subject="x" * 200, tutor="T",
            deadline="2025-12-31", details="ok",
            file_id=None, file_type=None,
        )
    mock_project_repo.add_project.assert_not_called()


@pytest.mark.asyncio
async def test_add_project_service_validates_deadline_format(mock_project_repo):
    service = AddProjectService(mock_project_repo)
    with pytest.raises(ValueError):
        await service.execute(
            user_id=1, username="u", user_full_name="U",
            subject="Math", tutor="T",
            deadline="not-a-date", details="ok",
            file_id=None, file_type=None,
        )
    mock_project_repo.add_project.assert_not_called()


@pytest.mark.asyncio
async def test_add_project_service_persists_on_valid_input(mock_project_repo):
    mock_project_repo.add_project.return_value = 42
    with patch(
        "infrastructure.repositories.Database.get_next_sequence",
        new=AsyncMock(return_value=42),
    ):
        service = AddProjectService(mock_project_repo)
        result = await service.execute(
            user_id=1, username="u", user_full_name="U",
            subject="Math", tutor="Dr. X",
            deadline="2025-12-31", details="Some details",
            file_id=None, file_type=None,
        )
    assert result == 42
    mock_project_repo.add_project.assert_called_once()


# ---------------------------------------------------------------------------
# VerifyProjectOwnershipService
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_verify_ownership_raises_for_wrong_user(mock_project_repo):
    mock_project_repo.get_project_by_id.return_value = {"id": 1, "user_id": 99}
    service = VerifyProjectOwnershipService(mock_project_repo)
    with pytest.raises(PermissionError):
        await service.execute(proj_id=1, user_id=1)  # user_id 1 ≠ owner 99


@pytest.mark.asyncio
async def test_verify_ownership_raises_when_not_found(mock_project_repo):
    mock_project_repo.get_project_by_id.return_value = None
    service = VerifyProjectOwnershipService(mock_project_repo)
    with pytest.raises(PermissionError):
        await service.execute(proj_id=1, user_id=1)


@pytest.mark.asyncio
async def test_verify_ownership_passes_for_correct_user(mock_project_repo):
    project = {"id": 1, "user_id": 5}
    mock_project_repo.get_project_by_id.return_value = project
    result = await VerifyProjectOwnershipService(mock_project_repo).execute(1, 5)
    assert result == project


# ---------------------------------------------------------------------------
# GetStudentProjectsService / GetStudentOffersService
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_student_projects_calls_repo(mock_project_repo):
    mock_cursor = MagicMock()
    mock_cursor.to_list = AsyncMock(return_value=[{"id": 1}])
    mock_project_repo.get_projects_by_status = AsyncMock(return_value=[{"id": 1}])

    result = await GetStudentProjectsService(mock_project_repo).execute(user_id=7)
    assert result == [{"id": 1}]
    mock_project_repo.get_projects_by_status.assert_called_once()
    _, kwargs = mock_project_repo.get_projects_by_status.call_args
    assert kwargs["user_id"] == 7


@pytest.mark.asyncio
async def test_get_student_offers_filters_by_offered_status(mock_project_repo):
    mock_project_repo.get_projects_by_status = AsyncMock(return_value=[])
    await GetStudentOffersService(mock_project_repo).execute(user_id=3)
    statuses, = mock_project_repo.get_projects_by_status.call_args[0]
    assert ProjectStatus.OFFERED in statuses


# ---------------------------------------------------------------------------
# GetProjectDetailService
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_project_detail_maps_fields(mock_project_repo):
    mock_project_repo.get_project_by_id.return_value = {
        "id": 5, "subject_name": "Math", "tutor_name": "Dr. X",
        "deadline": "2025-12-31", "details": "details", "file_id": None,
        "file_type": None, "user_id": 1, "user_full_name": "Ali", "username": "ali",
    }
    detail = await GetProjectDetailService(mock_project_repo).execute(5)
    assert isinstance(detail, ProjectDetail)
    assert detail.subject == "Math"
    assert detail.tutor == "Dr. X"
    assert detail.user_id == 1


@pytest.mark.asyncio
async def test_get_project_detail_returns_none_when_missing(mock_project_repo):
    mock_project_repo.get_project_by_id.return_value = None
    assert await GetProjectDetailService(mock_project_repo).execute(999) is None


# ---------------------------------------------------------------------------
# SendOfferService
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_offer_service_updates_and_returns_result(mock_project_repo):
    mock_project_repo.get_project_by_id.return_value = {
        "id": 1, "user_id": 7, "subject_name": "Physics"
    }
    result = await SendOfferService(mock_project_repo).execute(
        proj_id=1, price="50,000", delivery="2025-06-01", notes="—"
    )
    mock_project_repo.update_offer.assert_called_once_with(1, "50,000", "2025-06-01")
    mock_project_repo.update_status.assert_called_once_with(1, ProjectStatus.OFFERED)
    assert result.user_id == 7
    assert result.price == "50,000"


@pytest.mark.asyncio
async def test_send_offer_service_raises_when_project_missing(mock_project_repo):
    mock_project_repo.get_project_by_id.return_value = None
    with pytest.raises(ValueError, match="not found"):
        await SendOfferService(mock_project_repo).execute(1, "50", "2025-01-01", "")


# ---------------------------------------------------------------------------
# FinishProjectService
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_finish_project_service_marks_finished(mock_project_repo):
    mock_project_repo.get_project_by_id.return_value = {
        "id": 3, "user_id": 9, "subject_name": "CS"
    }
    result = await FinishProjectService(mock_project_repo).execute(3)
    mock_project_repo.update_status.assert_called_once_with(3, ProjectStatus.FINISHED)
    assert result.user_id == 9
    assert result.subject == "CS"


# ---------------------------------------------------------------------------
# DenyProjectService
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_deny_admin_sets_correct_status(mock_project_repo):
    mock_project_repo.get_project_by_id.return_value = {"id": 2, "user_id": 5}
    result = await DenyProjectService(mock_project_repo).execute_admin_deny(2)
    mock_project_repo.update_status.assert_called_once_with(2, ProjectStatus.DENIED_ADMIN)
    assert result.is_admin_deny is True
    assert result.student_user_id == 5


@pytest.mark.asyncio
async def test_deny_student_raises_for_wrong_owner(mock_project_repo):
    mock_project_repo.get_project_by_id.return_value = {"id": 2, "user_id": 99}
    with pytest.raises(PermissionError):
        await DenyProjectService(mock_project_repo).execute_student_deny(2, user_id=1)


@pytest.mark.asyncio
async def test_deny_student_sets_correct_status(mock_project_repo):
    mock_project_repo.get_project_by_id.return_value = {"id": 2, "user_id": 7}
    result = await DenyProjectService(mock_project_repo).execute_student_deny(2, user_id=7)
    mock_project_repo.update_status.assert_called_once_with(2, ProjectStatus.DENIED_STUDENT)
    assert result.is_admin_deny is False


# ---------------------------------------------------------------------------
# SubmitPaymentService
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_submit_payment_service(mock_project_repo, mock_payment_repo):
    mock_payment_repo.add_payment.return_value = 10
    result = await SubmitPaymentService(mock_project_repo, mock_payment_repo).execute(
        proj_id=3, user_id=1, file_id="f_abc", file_type="photo"
    )
    mock_payment_repo.add_payment.assert_called_once_with(3, 1, "f_abc")
    mock_project_repo.update_status.assert_called_once_with(3, ProjectStatus.AWAITING_VERIFICATION)
    assert result.payment_id == 10
    assert result.file_type == "photo"


@pytest.mark.asyncio
async def test_submit_payment_raises_without_proj_id(mock_project_repo, mock_payment_repo):
    with pytest.raises(ValueError, match="missing FSM state"):
        await SubmitPaymentService(mock_project_repo, mock_payment_repo).execute(
            proj_id=None, user_id=1, file_id="f", file_type=None
        )


# ---------------------------------------------------------------------------
# ConfirmPaymentService / RejectPaymentService
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_confirm_payment_service(mock_project_repo, mock_payment_repo):
    mock_payment_repo.get_payment.return_value = {"id": 5, "project_id": 2}
    mock_project_repo.get_project_by_id.return_value = {"user_id": 7, "subject_name": "Math"}

    result = await ConfirmPaymentService(mock_project_repo, mock_payment_repo).execute(5)

    mock_payment_repo.update_status.assert_called_once_with(5, PaymentStatus.ACCEPTED)
    mock_project_repo.update_status.assert_called_once_with(2, ProjectStatus.ACCEPTED)
    assert result.user_id == 7
    assert result.subject == "Math"


@pytest.mark.asyncio
async def test_confirm_payment_raises_when_not_found(mock_project_repo, mock_payment_repo):
    mock_payment_repo.get_payment.return_value = None
    with pytest.raises(ValueError, match="not found"):
        await ConfirmPaymentService(mock_project_repo, mock_payment_repo).execute(999)


@pytest.mark.asyncio
async def test_reject_payment_resets_project_to_offered(mock_project_repo, mock_payment_repo):
    mock_payment_repo.get_payment.return_value = {"id": 6, "project_id": 3}
    mock_project_repo.get_project_by_id.return_value = {"user_id": 4, "subject_name": "CS"}

    result = await RejectPaymentService(mock_project_repo, mock_payment_repo).execute(6)

    mock_payment_repo.update_status.assert_called_once_with(6, PaymentStatus.REJECTED)
    mock_project_repo.update_status.assert_called_once_with(3, ProjectStatus.OFFERED)
    assert result.proj_id == 3
