import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from domain.entities import ReferralUser, WithdrawalRequest
from domain.exceptions import (
    InsufficientBalanceError, WithdrawalAmountInvalidError,
    WithdrawalLimitError, WithdrawalTooLargeError, WithdrawalTooSmallError,
)
from infrastructure.repositories.user_referral import UserReferralRepository
from application.withdrawal_service import WithdrawalService


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.referral_users = MagicMock()
    db.referral_users.find_one_and_update = AsyncMock()
    db.referral_users.find_one = AsyncMock()
    db.referral_users.update_one = AsyncMock()
    db.referral_users.find = MagicMock()
    db.withdrawal_requests = MagicMock()
    db.withdrawal_requests.insert_one = AsyncMock()
    db.commission_logs = MagicMock()
    db.commission_logs.insert_one = AsyncMock()
    db.commission_logs.find = MagicMock()
    return db


@pytest.mark.asyncio
async def test_repo_get_or_create_user(mock_db):
    repo = UserReferralRepository(mock_db)
    mock_db.referral_users.find_one_and_update.return_value = {
        "user_id": 1, "balance": 0.0, "last_withdrawal_date": None,
        "created_at": datetime.now(timezone.utc), "referred_by": 2
    }
    user = await repo.get_or_create_user(1, 2)
    assert user.user_id == 1
    assert user.referred_by == 2
    await repo.get_or_create_user(3, 3)
    call_args = mock_db.referral_users.find_one_and_update.call_args[0]
    set_on_insert = call_args[1]["$setOnInsert"]
    assert "referred_by" not in set_on_insert


@pytest.mark.asyncio
async def test_repo_deduct_balance(mock_db):
    repo = UserReferralRepository(mock_db)
    mock_db.referral_users.find_one_and_update.return_value = {"user_id": 1, "balance": 1000}
    await repo.deduct_balance(1, 500)
    mock_db.referral_users.find_one_and_update.return_value = None
    with pytest.raises(InsufficientBalanceError):
        await repo.deduct_balance(1, 5000)


@pytest.mark.asyncio
async def test_repo_add_balance_raises_if_user_missing(mock_db):
    """add_balance must raise RuntimeError when user doc is not found (no upsert)."""
    repo = UserReferralRepository(mock_db)
    result_mock = MagicMock()
    result_mock.matched_count = 0
    mock_db.referral_users.update_one.return_value = result_mock
    with pytest.raises(RuntimeError, match="not found"):
        await repo.add_balance(999, 100.0)


@pytest.mark.asyncio
async def test_repo_add_balance_success(mock_db):
    """add_balance succeeds when the user document exists."""
    repo = UserReferralRepository(mock_db)
    result_mock = MagicMock()
    result_mock.matched_count = 1
    mock_db.referral_users.update_one.return_value = result_mock
    await repo.add_balance(1, 100.0)


@pytest.mark.asyncio
async def test_withdrawal_service_success(mock_db):
    repo = UserReferralRepository(mock_db)
    service = WithdrawalService(repo)
    user_doc = {
        "user_id": 1, "balance": 2000.0, "last_withdrawal_date": None,
        "created_at": datetime.now(timezone.utc)
    }
    # First call: pre-check; second call: post-deduction re-fetch
    mock_db.referral_users.find_one.side_effect = [user_doc, {**user_doc, "balance": 1000.0}]
    result_mock = MagicMock()
    result_mock.matched_count = 1
    mock_db.referral_users.update_one.return_value = result_mock
    mock_db.referral_users.find_one_and_update.return_value = {"user_id": 1, "balance": 2000.0}
    cursor_mock = AsyncMock()
    cursor_mock.to_list.return_value = []
    mock_db.referral_users.find.return_value = cursor_mock
    mock_db.commission_logs.find.return_value = cursor_mock
    req, tg_summary, txt_report = await service.request_withdrawal(
        user_id=1, amount=1000.0, shamcash_address="09xx", shamcash_name="Ali"
    )
    assert req.amount == 1000.0
    assert "Ali" in txt_report
    assert "1000" in tg_summary


@pytest.mark.asyncio
async def test_withdrawal_service_amount_invalid():
    """Zero and negative amounts must raise WithdrawalAmountInvalidError."""
    repo = AsyncMock()
    service = WithdrawalService(repo)
    with pytest.raises(WithdrawalAmountInvalidError):
        await service.request_withdrawal(1, 0.0, "09xx", "Ali")
    with pytest.raises(WithdrawalAmountInvalidError):
        await service.request_withdrawal(1, -100.0, "09xx", "Ali")


@pytest.mark.asyncio
async def test_withdrawal_service_too_small():
    repo = AsyncMock()
    service = WithdrawalService(repo)
    with pytest.raises(WithdrawalTooSmallError):
        await service.request_withdrawal(1, 400.0, "09xx", "Ali")


@pytest.mark.asyncio
async def test_withdrawal_service_too_large():
    """Amounts over the maximum must raise WithdrawalTooLargeError."""
    repo = AsyncMock()
    service = WithdrawalService(repo)
    with pytest.raises(WithdrawalTooLargeError):
        await service.request_withdrawal(1, 2_000_000.0, "09xx", "Ali")


@pytest.mark.asyncio
async def test_withdrawal_service_daily_limit():
    repo = AsyncMock()
    service = WithdrawalService(repo)
    today_iso = datetime.now(timezone.utc).date().isoformat()
    user_mock = ReferralUser(
        user_id=1, balance=2000.0,
        last_withdrawal_date=today_iso,
        created_at=datetime.now(timezone.utc),
    )
    repo.get_user.return_value = user_mock
    with pytest.raises(WithdrawalLimitError):
        await service.request_withdrawal(1, 1000.0, "09xx", "Ali")
