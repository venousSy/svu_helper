import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from dashboard_api.services.projects_service import _safe_price, _to_project_response, get_projects_page, get_project_details, get_urgent_projects_list
from fastapi import HTTPException

def test_safe_price():
    assert _safe_price(None) is None
    assert _safe_price("150") == 150
    assert _safe_price(150.5) == 150
    assert _safe_price("invalid") is None

def test_to_project_response():
    res = _to_project_response({"_id": "abc", "id": 1, "price": "100", "subject_name": "S", "user_id": 1, "status": "pending", "tutor_name": "T", "deadline": "2026", "created_at": "2026"})
    assert res is not None
    assert res.id == 1
    assert res.price == 100
    
    assert _to_project_response({"missing": "fields"}) is None

@pytest.mark.asyncio
@patch("dashboard_api.services.projects_service.count_projects")
@patch("dashboard_api.services.projects_service.get_paginated_projects")
async def test_get_projects_page(mock_get, mock_count):
    mock_count.return_value = 10
    mock_get.return_value = [{"id": 1, "subject_name": "S", "user_id": 1, "status": "pending", "tutor_name": "T", "deadline": "2026", "created_at": "2026"}]
    
    res = await get_projects_page(1, 5)
    assert res.total == 10
    assert res.pages == 2
    assert len(res.items) == 1

@pytest.mark.asyncio
async def test_get_project_details():
    mock_proj_repo = AsyncMock()
    mock_pay_repo = AsyncMock()
    
    # Not found
    mock_proj_repo.get_project_by_id.return_value = None
    with pytest.raises(HTTPException) as exc:
        await get_project_details(mock_proj_repo, mock_pay_repo, 1)
    assert exc.value.status_code == 404
    
    # Found without payment
    mock_proj_repo.get_project_by_id.return_value = {"id": 1, "subject_name": "S", "user_id": 1, "status": "pending", "tutor_name": "T", "deadline": "2026", "created_at": "2026", "details": "d"}
    mock_pay_repo.get_payment_by_project_id.return_value = None
    res = await get_project_details(mock_proj_repo, mock_pay_repo, 1)
    assert res.payment is None
    assert res.id == 1
    
    # Found with payment
    mock_pay_repo.get_payment_by_project_id.return_value = {"id": 1, "project_id": 1, "user_id": 1, "file_id": "f", "status": "pending"}
    res = await get_project_details(mock_proj_repo, mock_pay_repo, 1)
    assert res.payment is not None
    assert res.payment.file_id == "f"

@pytest.mark.asyncio
async def test_get_urgent_projects_list():
    mock_repo = AsyncMock()
    mock_repo.get_urgent_projects.return_value = [{"id": 1, "subject_name": "S", "user_id": 1, "status": "pending", "tutor_name": "T", "deadline": "2026", "created_at": "2026"}]
    res = await get_urgent_projects_list(mock_repo)
    assert len(res) == 1
