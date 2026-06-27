import pytest
from unittest.mock import AsyncMock
from application.project_service import (
    AddProjectService, GetStudentProjectDetailService,
    GetStudentProjectsService, GetStudentOffersService
)

@pytest.mark.asyncio
async def test_add_project_service():
    repo = AsyncMock()
    service = AddProjectService(repo)
    
    # Validation errors
    with pytest.raises(ValueError, match="Subject too long"):
        await service.execute(user_id=1, username="u", user_full_name="n", subject="A"*200, tutor="T", deadline="2030-01-01", details="D", attachments=[])
        
    with pytest.raises(ValueError, match="Tutor name too long"):
        await service.execute(user_id=1, username="u", user_full_name="n", subject="S", tutor="T"*200, deadline="2030-01-01", details="D", attachments=[])
        
    with pytest.raises(ValueError, match="Details too long"):
        await service.execute(user_id=1, username="u", user_full_name="n", subject="S", tutor="T", deadline="2030-01-01", details="D"*4000, attachments=[])
        
    with pytest.raises(ValueError): # from parse_deadline
        await service.execute(user_id=1, username="u", user_full_name="n", subject="S", tutor="T", deadline="invalid", details="D", attachments=[])
        
    # Success
    repo.add_project.return_value = 1
    result = await service.execute(user_id=1, username="u", user_full_name="n", subject="S", tutor="T", deadline="2030-01-01", details="D", attachments=[])
    assert result == 1
    repo.add_project.assert_called_once()

@pytest.mark.asyncio
async def test_get_student_project_detail_service():
    repo = AsyncMock()
    service = GetStudentProjectDetailService(repo)
    
    # Not found
    repo.get_project_by_id.return_value = None
    with pytest.raises(PermissionError):
        await service.execute(1, 123)
        
    # Not owner
    repo.get_project_by_id.return_value = {"user_id": 999}
    with pytest.raises(PermissionError):
        await service.execute(1, 123)
        
    # Success
    repo.get_project_by_id.return_value = {"user_id": 123}
    result = await service.execute(1, 123)
    assert result["user_id"] == 123

@pytest.mark.asyncio
async def test_get_student_projects_service():
    repo = AsyncMock()
    service = GetStudentProjectsService(repo)
    await service.execute(123)
    repo.get_projects_by_status.assert_called_once()

@pytest.mark.asyncio
async def test_get_student_offers_service():
    repo = AsyncMock()
    service = GetStudentOffersService(repo)
    await service.execute(123)
    repo.get_projects_by_status.assert_called_once()
