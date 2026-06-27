import pytest
from unittest.mock import AsyncMock
from application.offer_service import (
    GetProjectDetailService, SendOfferService, FinishProjectService, DenyProjectService
)
from domain.enums import ProjectStatus

@pytest.mark.asyncio
async def test_get_project_detail_service():
    repo = AsyncMock()
    service = GetProjectDetailService(repo)
    
    # Not found
    repo.get_project_by_id.return_value = None
    assert await service.execute(1) is None
    
    # Found
    repo.get_project_by_id.return_value = {
        "id": 1, "subject_name": "S", "tutor_name": "T", "deadline": "2026-01-01",
        "details": "D", "user_id": 123
    }
    result = await service.execute(1)
    assert result.proj_id == 1
    assert result.user_full_name == "Unknown"
    assert result.attachments == []

@pytest.mark.asyncio
async def test_send_offer_service():
    repo = AsyncMock()
    service = SendOfferService(repo)
    
    # Not found
    repo.get_project_by_id.return_value = None
    with pytest.raises(ValueError, match="not found"):
        await service.execute(1, "100", "tomorrow", "notes")
    
    # Found
    repo.get_project_by_id.return_value = {"user_id": 123, "subject_name": "S"}
    result = await service.execute(1, "100", "tomorrow", "notes")
    assert result.user_id == 123
    repo.update_offer.assert_called_once_with(1, "100", "tomorrow")
    repo.update_status.assert_called_once_with(1, ProjectStatus.OFFERED)

@pytest.mark.asyncio
async def test_finish_project_service():
    repo = AsyncMock()
    service = FinishProjectService(repo)
    
    # Not found
    repo.get_project_by_id.return_value = None
    with pytest.raises(ValueError, match="not found"):
        await service.execute(1)
    
    # Found
    repo.get_project_by_id.return_value = {"user_id": 123, "subject_name": "S"}
    result = await service.execute(1)
    assert result.user_id == 123
    repo.update_status.assert_called_once_with(1, ProjectStatus.FINISHED)

@pytest.mark.asyncio
async def test_deny_project_service():
    repo = AsyncMock()
    service = DenyProjectService(repo)
    
    # Admin Deny
    repo.get_project_by_id.return_value = {"user_id": 123}
    result = await service.execute_admin_deny(1)
    assert result.is_admin_deny is True
    assert result.student_user_id == 123
    repo.update_status.assert_called_with(1, ProjectStatus.DENIED_ADMIN)
    
    # Admin Deny Missing project
    repo.get_project_by_id.return_value = None
    result = await service.execute_admin_deny(1)
    assert result.student_user_id is None
    
    # Student Deny Not Found or Not Owner
    repo.get_project_by_id.return_value = None
    with pytest.raises(PermissionError):
        await service.execute_student_deny(1, 123)
        
    repo.get_project_by_id.return_value = {"user_id": 999}
    with pytest.raises(PermissionError):
        await service.execute_student_deny(1, 123)
        
    # Student Deny Success
    repo.get_project_by_id.return_value = {"user_id": 123}
    result = await service.execute_student_deny(1, 123)
    assert result.is_admin_deny is False
    assert result.student_user_id is None
    repo.update_status.assert_called_with(1, ProjectStatus.DENIED_STUDENT)
