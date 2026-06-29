"""
WithdrawalService
=================
All business logic for ShamCash balance withdrawals.
Handlers call this and send the resulting report — no business logic in handlers.
"""
from datetime import datetime, timezone
from typing import Tuple

import structlog

from domain.entities import WithdrawalRequest
from domain.exceptions import (
    InsufficientBalanceError,
    WithdrawalAmountInvalidError,
    WithdrawalLimitError,
    WithdrawalTooLargeError,
    WithdrawalTooSmallError,
)
from infrastructure.repositories.user_referral import UserReferralRepository
from utils.report_builder import build_withdrawal_report

logger = structlog.get_logger(__name__)

MINIMUM_WITHDRAWAL_SYP: float = 500.0
MAXIMUM_WITHDRAWAL_SYP: float = 1_000_000.0


class WithdrawalService:
    def __init__(self, user_referral_repo: UserReferralRepository) -> None:
        self._repo = user_referral_repo

    async def request_withdrawal(
        self,
        user_id: int,
        amount: float,
        shamcash_address: str,
        shamcash_name: str,
    ) -> Tuple[WithdrawalRequest, str, str]:
        """
        Validates and processes a withdrawal request.

        Returns:
            (WithdrawalRequest, telegram_summary: str, txt_report: str)

        Raises:
            WithdrawalTooSmallError
            WithdrawalLimitError
            InsufficientBalanceError
        """
        # 1. Positive-value guard
        if amount <= 0:
            raise WithdrawalAmountInvalidError(f"Amount {amount} is not positive")

        # 2. Minimum check
        if amount < MINIMUM_WITHDRAWAL_SYP:
            raise WithdrawalTooSmallError(f"Amount {amount} below minimum {MINIMUM_WITHDRAWAL_SYP} SYP")

        # 3. Maximum check
        if amount > MAXIMUM_WITHDRAWAL_SYP:
            raise WithdrawalTooLargeError(f"Amount {amount} exceeds maximum {MAXIMUM_WITHDRAWAL_SYP} SYP")

        # 4. Daily limit check
        user = await self._repo.get_user(user_id)
        today_iso = datetime.now(timezone.utc).date().isoformat()
        if user and user.last_withdrawal_date == today_iso:
            raise WithdrawalLimitError(f"User {user_id} already requested today")

        # 5. Deduct balance (raises InsufficientBalanceError atomically if short)
        await self._repo.deduct_balance(user_id, amount)

        # 6. Record date (prevents second request today)
        await self._repo.record_withdrawal_date(user_id)

        # 7. Build and persist the request
        req = WithdrawalRequest(
            user_id=user_id,
            amount=amount,
            shamcash_address=shamcash_address,
            shamcash_name=shamcash_name,
        )
        await self._repo.save_withdrawal_request(req)

        # 8. Fetch data for the audit report
        # Re-fetch the user to get the accurate post-deduction balance
        updated_user = await self._repo.get_user(user_id)
        referral_ids = await self._repo.get_referrals(user_id)
        commission_logs = await self._repo.get_commission_logs_for_referrer(user_id)
        remaining_balance = updated_user.balance if updated_user else 0.0

        # 7. Build the dual-format report
        telegram_summary, txt_report = build_withdrawal_report(
            user_id=user_id,
            req=req,
            referral_ids=referral_ids,
            commission_logs=commission_logs,
            remaining_balance=max(remaining_balance, 0.0),
        )

        logger.info("Withdrawal processed", user_id=user_id, amount=amount,
                    request_id=req.request_id)
        return req, telegram_summary, txt_report
