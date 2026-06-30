import structlog
from datetime import datetime, timezone
from typing import List, Optional

from domain.entities import CommissionLog, ReferralUser, WithdrawalRequest
from domain.exceptions import InsufficientBalanceError

logger = structlog.get_logger(__name__)

class UserReferralRepository:
    """Manages the `referral_users`, `withdrawal_requests`, and
    `commission_logs` collections."""

    def __init__(self, db) -> None:
        self._db = db

    # ── ReferralUser ────────────────────────────────────────────────────────

    async def get_or_create_user(
        self, user_id: int, referred_by: Optional[int] = None
    ) -> ReferralUser:
        """
        Atomically upserts the user document.
        - `referred_by` is only written on INSERT ($setOnInsert), never on UPDATE.
        - If referred_by == user_id, it is silently set to None (self-referral guard).
        """
        safe_referred_by = None if referred_by == user_id else referred_by

        set_on_insert: dict = {"balance": 0.0, "last_withdrawal_date": None,
                               "created_at": datetime.now(timezone.utc)}
        if safe_referred_by is not None:
            set_on_insert["referred_by"] = safe_referred_by

        from pymongo import ReturnDocument
        doc = await self._db.referral_users.find_one_and_update(
            {"user_id": user_id},
            {"$setOnInsert": set_on_insert},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return ReferralUser(**doc)

    async def get_user(self, user_id: int) -> Optional[ReferralUser]:
        doc = await self._db.referral_users.find_one({"user_id": user_id})
        return ReferralUser(**doc) if doc else None

    async def add_balance(self, user_id: int, amount: float) -> None:
        """Atomically increments the user's balance.

        Raises:
            RuntimeError: if the user document doesn't exist (data integrity bug).
        """
        result = await self._db.referral_users.update_one(
            {"user_id": user_id}, {"$inc": {"balance": amount}}
        )
        if result.matched_count == 0:
            raise RuntimeError(
                f"add_balance: user {user_id} not found — cannot credit balance"
            )
        logger.info("Balance credited", user_id=user_id, amount=amount)

    async def deduct_balance(self, user_id: int, amount: float) -> None:
        """
        Atomically deducts `amount` only if balance >= amount.
        Raises InsufficientBalanceError otherwise.
        """
        result = await self._db.referral_users.find_one_and_update(
            {"user_id": user_id, "balance": {"$gte": amount}},
            {"$inc": {"balance": -amount}},
        )
        if result is None:
            raise InsufficientBalanceError(
                f"User {user_id} has insufficient balance for {amount}"
            )
        logger.info("Balance deducted", user_id=user_id, amount=amount)

    async def record_withdrawal_date(self, user_id: int) -> None:
        """Stamps today's UTC date to enforce the 1/day limit."""
        today = datetime.now(timezone.utc).date().isoformat()  # "YYYY-MM-DD"
        await self._db.referral_users.update_one(
            {"user_id": user_id}, {"$set": {"last_withdrawal_date": today}}
        )

    async def get_referrals(self, user_id: int) -> List[int]:
        """Returns user_ids of all users who registered via this user's link."""
        cursor = self._db.referral_users.find(
            {"referred_by": user_id}, {"user_id": 1}
        )
        docs = await cursor.to_list(length=500)
        return [d["user_id"] for d in docs]

    # ── WithdrawalRequest ────────────────────────────────────────────────────

    async def save_withdrawal_request(self, req: WithdrawalRequest) -> None:
        await self._db.withdrawal_requests.insert_one(req.model_dump())
        logger.info("Withdrawal request saved", user_id=req.user_id,
                    request_id=req.request_id, amount=req.amount)

    async def mark_withdrawal_paid(
        self,
        request_id: str,
        processed_by: str,
        shamcash_ref: Optional[str] = None,
    ) -> dict:
        """
        Atomically marks a pending withdrawal as processed.

        Returns the updated document.
        Raises ValueError if the request is not found or already processed (double-pay guard).
        """
        from pymongo import ReturnDocument
        update: dict = {
            "status": "processed",
            "processed_at": datetime.now(timezone.utc),
            "processed_by": processed_by,
        }
        if shamcash_ref:
            update["shamcash_ref"] = shamcash_ref.strip()

        doc = await self._db.withdrawal_requests.find_one_and_update(
            {"request_id": request_id, "status": "pending"},
            {"$set": update},
            return_document=ReturnDocument.AFTER,
        )
        if doc is None:
            existing = await self._db.withdrawal_requests.find_one({"request_id": request_id})
            if existing is None:
                raise ValueError(f"Withdrawal request '{request_id}' not found")
            raise ValueError(
                f"Withdrawal request '{request_id}' is already '{existing['status']}'"
            )
        logger.info("Withdrawal paid via bot", request_id=request_id,
                    user_id=doc["user_id"], amount=doc["amount"], by=processed_by)
        return doc

    async def reject_withdrawal(
        self,
        request_id: str,
        processed_by: str,
    ) -> dict:
        """
        Atomically marks a pending withdrawal as rejected.
        Does NOT restore the balance — caller must call restore_balance() explicitly.

        Raises ValueError if not found or already processed.
        """
        from pymongo import ReturnDocument
        doc = await self._db.withdrawal_requests.find_one_and_update(
            {"request_id": request_id, "status": "pending"},
            {"$set": {
                "status": "rejected",
                "processed_at": datetime.now(timezone.utc),
                "processed_by": processed_by,
            }},
            return_document=ReturnDocument.AFTER,
        )
        if doc is None:
            existing = await self._db.withdrawal_requests.find_one({"request_id": request_id})
            if existing is None:
                raise ValueError(f"Withdrawal request '{request_id}' not found")
            raise ValueError(
                f"Withdrawal request '{request_id}' is already '{existing['status']}'"
            )
        logger.info("Withdrawal rejected via bot", request_id=request_id,
                    user_id=doc["user_id"], amount=doc["amount"], by=processed_by)
        return doc

    async def restore_balance(self, user_id: int, amount: float) -> None:
        """Atomically restores a user's balance (used after withdrawal rejection)."""
        await self._db.referral_users.update_one(
            {"user_id": user_id},
            {"$inc": {"balance": amount}},
        )
        logger.info("Balance restored after rejection", user_id=user_id, amount=amount)

    async def get_all_withdrawal_requests(
        self, status_filter: Optional[str] = None
    ) -> List[dict]:
        """Lists all withdrawal requests, optionally filtered by status."""
        query = {}
        if status_filter:
            query["status"] = status_filter
        cursor = self._db.withdrawal_requests.find(query).sort("requested_at", -1)
        return await cursor.to_list(length=500)

    # ── CommissionLog ────────────────────────────────────────────────────────

    async def save_commission_log(self, log: CommissionLog) -> None:
        await self._db.commission_logs.insert_one(log.model_dump())
        logger.info("Commission log saved", referrer_id=log.referrer_id,
                    project_id=log.project_id, commission=log.commission_amount)

    async def get_commission_logs_for_referrer(
        self, referrer_id: int
    ) -> List[CommissionLog]:
        cursor = self._db.commission_logs.find({"referrer_id": referrer_id})
        docs = await cursor.to_list(length=500)
        return [CommissionLog(**d) for d in docs]
