import pytest
from unittest.mock import AsyncMock
from application.matchmaking_service import (
    CreateTeamRequestService,
    FindOpenTeamsService,
    JoinTeamService,
    HandleJoinDecisionService,
    ManageTeamService,
)
from domain.enums import TeamRequestStatus, MatchStatus

@pytest.mark.asyncio
async def test_create_team_request_service_validation():
    mock_repo = AsyncMock()
    service = CreateTeamRequestService(mock_repo)
    
    with pytest.raises(ValueError, match="Invalid course name"):
        await service.execute(
            host_id=1, host_name="A", host_username="a", course_name="",
            doctor_name="Dr. B", specialization="IT", required_members=2
        )
        
    with pytest.raises(ValueError, match="Required members must be 1, 2, or 3."):
        await service.execute(
            host_id=1, host_name="A", host_username="a", course_name="Math",
            doctor_name="Dr. B", specialization="IT", required_members=4
        )

@pytest.mark.asyncio
async def test_create_team_request_service_existing_global():
    mock_repo = AsyncMock()
    mock_repo.has_global_open_team_for_subject.return_value = True
    service = CreateTeamRequestService(mock_repo)
    
    with pytest.raises(ValueError, match="global_team_exists"):
        await service.execute(
            host_id=1, host_name="A", host_username="a", course_name="Math",
            doctor_name="Dr. B", specialization="IT", required_members=2
        )

@pytest.mark.asyncio
async def test_create_team_request_service_existing_involvement():
    mock_repo = AsyncMock()
    mock_repo.has_global_open_team_for_subject.return_value = False
    mock_repo.has_active_involvement_for_course.return_value = True
    service = CreateTeamRequestService(mock_repo)
    
    with pytest.raises(ValueError, match="active_involvement_exists"):
        await service.execute(
            host_id=1, host_name="A", host_username="a", course_name="Math",
            doctor_name="Dr. B", specialization="IT", required_members=2
        )

@pytest.mark.asyncio
async def test_create_team_request_service_success():
    mock_repo = AsyncMock()
    mock_repo.has_global_open_team_for_subject.return_value = False
    mock_repo.has_active_involvement_for_course.return_value = False
    mock_repo.create_team_request.return_value = 123
    service = CreateTeamRequestService(mock_repo)
    
    result = await service.execute(
        host_id=1, host_name="A", host_username="a", course_name="Math",
        doctor_name="Dr. B", specialization="IT", required_members=2
    )
    assert result == 123
    mock_repo.create_team_request.assert_called_once()

@pytest.mark.asyncio
async def test_find_open_teams_service():
    mock_repo = AsyncMock()
    service = FindOpenTeamsService(mock_repo)
    await service.execute("IT", 1)
    mock_repo.get_open_teams_for_specialization.assert_called_once_with("IT", 1)
    
    await service.get_user_pending_joins(1)
    mock_repo.get_user_pending_joins.assert_called_once_with(1)

@pytest.mark.asyncio
async def test_join_team_service():
    mock_repo = AsyncMock()
    service = JoinTeamService(mock_repo)
    
    # not found
    mock_repo.get_by_id.return_value = None
    with pytest.raises(ValueError, match="not_found"):
        await service.execute(1, 2, "B")
        
    # closed
    mock_repo.get_by_id.return_value = {"status": TeamRequestStatus.CLOSED.value}
    with pytest.raises(ValueError, match="closed"):
        await service.execute(1, 2, "B")
        
    # own team
    mock_repo.get_by_id.return_value = {"status": TeamRequestStatus.OPEN.value, "host_id": 2}
    with pytest.raises(ValueError, match="own_team"):
        await service.execute(1, 2, "B")

    # already member
    mock_repo.get_by_id.return_value = {"status": TeamRequestStatus.OPEN.value, "host_id": 1, "current_members": [2]}
    with pytest.raises(ValueError, match="already_member"):
        await service.execute(1, 2, "B")

    # duplicate
    mock_repo.get_by_id.return_value = {"status": TeamRequestStatus.OPEN.value, "host_id": 1, "current_members": [], "course_name": "Math"}
    mock_repo.has_join_request.return_value = True
    with pytest.raises(ValueError, match="duplicate"):
        await service.execute(1, 2, "B")

    # active involvement
    mock_repo.has_join_request.return_value = False
    mock_repo.has_active_involvement_for_course.return_value = True
    with pytest.raises(ValueError, match="active_involvement_exists"):
        await service.execute(1, 2, "B")

    # success
    mock_repo.has_active_involvement_for_course.return_value = False
    team = {"status": TeamRequestStatus.OPEN.value, "host_id": 1, "current_members": [], "course_name": "Math"}
    mock_repo.get_by_id.return_value = team
    result = await service.execute(1, 2, "B")
    assert result == team
    mock_repo.add_join_request.assert_called_once_with(1, 2, "B")

@pytest.mark.asyncio
async def test_handle_join_decision_service_accept():
    mock_repo = AsyncMock()
    service = HandleJoinDecisionService(mock_repo)
    
    # already full before accept
    mock_repo.get_by_id.return_value = {"current_members": [1, 2], "required_members": 2}
    with pytest.raises(ValueError, match="team_full"):
        await service.accept(1, 3)
        
    # atomic accept fails
    mock_repo.get_by_id.return_value = {"current_members": [1], "required_members": 2}
    mock_repo.atomic_accept_member.return_value = False
    with pytest.raises(ValueError, match="team_full"):
        await service.accept(1, 3)
        
    # success not full
    mock_repo.atomic_accept_member.return_value = True
    mock_repo.get_by_id.side_effect = [
        {"current_members": [1], "required_members": 3},  # First check
        {"current_members": [1, 3], "required_members": 3} # Second check
    ]
    result = await service.accept(1, 3)
    assert result["is_full"] is False
    mock_repo.close_request.assert_not_called()
    
    # success full
    mock_repo.get_by_id.side_effect = [
        {"current_members": [1], "required_members": 2},  # First check
        {"current_members": [1, 3], "required_members": 2} # Second check
    ]
    result = await service.accept(1, 3)
    assert result["is_full"] is True
    mock_repo.close_request.assert_called_once_with(1)
    mock_repo.reject_all_pending_joins.assert_called_once_with(1)

@pytest.mark.asyncio
async def test_handle_join_decision_service_reject():
    mock_repo = AsyncMock()
    service = HandleJoinDecisionService(mock_repo)
    mock_repo.get_by_id.return_value = {"id": 1}
    
    result = await service.reject(1, 2)
    assert result == {"id": 1}
    mock_repo.update_join_request_status.assert_called_once_with(1, 2, MatchStatus.REJECTED)

@pytest.mark.asyncio
async def test_manage_team_service():
    mock_repo = AsyncMock()
    service = ManageTeamService(mock_repo)
    
    # close not authorized
    mock_repo.get_by_id.return_value = None
    with pytest.raises(ValueError, match="not_authorized"):
        await service.close_team(1, 2)
    
    mock_repo.get_by_id.return_value = {"host_id": 1}
    with pytest.raises(ValueError, match="not_authorized"):
        await service.close_team(1, 2)

    # close success
    await service.close_team(1, 1)
    mock_repo.close_request.assert_called_once_with(1)
    
    # delete not authorized
    with pytest.raises(ValueError, match="not_authorized"):
        await service.delete_team(1, 2)
        
    # delete success
    await service.delete_team(1, 1)
    mock_repo.delete_request.assert_called_once_with(1)
    
    # withdraw not found
    mock_repo.get_by_id.return_value = None
    with pytest.raises(ValueError, match="not_found"):
        await service.withdraw_join(1, 2)
        
    # withdraw success
    mock_repo.get_by_id.return_value = {"host_id": 1}
    await service.withdraw_join(1, 2)
    mock_repo.remove_join_request.assert_called_once_with(1, 2)
