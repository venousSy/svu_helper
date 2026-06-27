import pytest
from unittest.mock import AsyncMock
from application.admin_service import (
    GetCategorizedProjectsService,
    GetPendingProjectsService,
    GetOngoingProjectsService,
    GetProjectHistoryService,
    GetAllPaymentsService,
    GetStatsService,
    MaintenanceService,
    GetAllUserIdsService,
)
from domain.enums import ProjectStatus

@pytest.mark.asyncio
async def test_get_categorized_projects_service():
    mock_repo = AsyncMock()
    mock_repo.get_all_categorized.return_value = {"pending": []}
    service = GetCategorizedProjectsService(mock_repo)
    result = await service.execute()
    assert result == {"pending": []}
    mock_repo.get_all_categorized.assert_called_once()

@pytest.mark.asyncio
async def test_get_pending_projects_service():
    mock_repo = AsyncMock()
    service = GetPendingProjectsService(mock_repo)
    await service.execute()
    mock_repo.get_projects_by_status.assert_called_once_with([ProjectStatus.PENDING])

@pytest.mark.asyncio
async def test_get_ongoing_projects_service():
    mock_repo = AsyncMock()
    service = GetOngoingProjectsService(mock_repo)
    await service.execute()
    mock_repo.get_projects_by_status.assert_called_once_with(
        [ProjectStatus.ACCEPTED, ProjectStatus.AWAITING_VERIFICATION]
    )

@pytest.mark.asyncio
async def test_get_project_history_service():
    mock_repo = AsyncMock()
    service = GetProjectHistoryService(mock_repo)
    await service.execute()
    mock_repo.get_projects_by_status.assert_called_once_with(
        [
            ProjectStatus.FINISHED,
            ProjectStatus.DENIED_ADMIN,
            ProjectStatus.DENIED_STUDENT,
            ProjectStatus.REJECTED_PAYMENT,
        ]
    )

@pytest.mark.asyncio
async def test_get_all_payments_service():
    mock_repo = AsyncMock()
    service = GetAllPaymentsService(mock_repo)
    await service.execute()
    mock_repo.get_all.assert_called_once()

@pytest.mark.asyncio
async def test_get_stats_service():
    mock_repo = AsyncMock()
    service = GetStatsService(mock_repo)
    await service.execute()
    mock_repo.get_stats.assert_called_once()

@pytest.mark.asyncio
async def test_maintenance_service():
    mock_repo = AsyncMock()
    service = MaintenanceService(mock_repo)
    
    await service.enable()
    mock_repo.set_maintenance_mode.assert_called_once_with(True)
    
    mock_repo.reset_mock()
    
    await service.disable()
    mock_repo.set_maintenance_mode.assert_called_once_with(False)

@pytest.mark.asyncio
async def test_get_all_user_ids_service():
    mock_repo = AsyncMock()
    mock_repo.get_all_user_ids.return_value = [1, 2, 3]
    service = GetAllUserIdsService(mock_repo)
    assert await service.execute() == [1, 2, 3]
    mock_repo.get_all_user_ids.assert_called_once()
