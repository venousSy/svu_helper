import pytest
from unittest.mock import AsyncMock
from application.payment_service import (
    SubmitPaymentService, ConfirmPaymentService, RejectPaymentService
)
from domain.enums import ProjectStatus, PaymentStatus

@pytest.mark.asyncio
async def test_submit_payment_service():
    proj_repo = AsyncMock()
    pay_repo = AsyncMock()
    service = SubmitPaymentService(proj_repo, pay_repo)
    
    # Missing proj_id
    with pytest.raises(ValueError, match="No active project"):
        await service.execute(0, 123, "f1", None)
        
    # Success
    pay_repo.add_payment.return_value = 1
    result = await service.execute(10, 123, "f1", "photo")
    assert result.payment_id == 1
    pay_repo.add_payment.assert_called_once_with(10, 123, "f1", file_type="photo")
    proj_repo.update_status.assert_called_once_with(10, ProjectStatus.AWAITING_VERIFICATION)

@pytest.mark.asyncio
async def test_confirm_payment_service():
    proj_repo = AsyncMock()
    pay_repo = AsyncMock()
    user_referral_repo = AsyncMock()
    service = ConfirmPaymentService(proj_repo, pay_repo, user_referral_repo)
    
    # Missing payment
    pay_repo.get_payment.return_value = None
    with pytest.raises(ValueError, match="not found"):
        await service.execute(1)
        
    # Success
    pay_repo.get_payment.return_value = {"project_id": 10}
    proj_repo.get_project_by_id.return_value = {"user_id": 123, "subject_name": "S"}
    result = await service.execute(1)
    assert result.user_id == 123
    assert result.proj_id == 10
    pay_repo.update_status.assert_called_once_with(1, PaymentStatus.ACCEPTED)
    proj_repo.update_status.assert_called_once_with(10, ProjectStatus.ACCEPTED)

@pytest.mark.asyncio
async def test_reject_payment_service():
    proj_repo = AsyncMock()
    pay_repo = AsyncMock()
    service = RejectPaymentService(proj_repo, pay_repo)
    
    # Missing payment
    pay_repo.get_payment.return_value = None
    with pytest.raises(ValueError, match="not found"):
        await service.execute(1)
        
    # Success with project
    pay_repo.get_payment.return_value = {"project_id": 10}
    proj_repo.get_project_by_id.return_value = {"user_id": 123, "subject_name": "S"}
    result = await service.execute(1)
    assert result.user_id == 123
    pay_repo.update_status.assert_called_once_with(1, PaymentStatus.REJECTED)
    proj_repo.update_status.assert_called_once_with(10, ProjectStatus.OFFERED)
    
    # Success without project
    proj_repo.get_project_by_id.return_value = None
    result = await service.execute(1)
    assert result.user_id == 0
    assert result.subject == ""
