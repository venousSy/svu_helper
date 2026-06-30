"""
Dashboard Withdrawals Repository
=================================
Queries the `withdrawal_requests` and `referral_users` collections
for the admin dashboard withdrawal management page.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog

from infrastructure.mongo_db import get_db

logger = structlog.get_logger(__name__)


async def get_all_requests(status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Returns all withdrawal requests, joined with the user's current balance.

    Args:
        status_filter: "pending" | "processed" | "rejected" | None (= all)
    """
    db = await get_db()
    match: Dict[str, Any] = {}
    if status_filter and status_filter != "all":
        match["status"] = status_filter

    pipeline = [
        {"$match": match},
        {"$sort": {"requested_at": -1}},
        {
            "$lookup": {
                "from": "referral_users",
                "localField": "user_id",
                "foreignField": "user_id",
                "as": "_user",
            }
        },
        {
            "$addFields": {
                "current_balance": {
                    "$ifNull": [{"$arrayElemAt": ["$_user.balance", 0]}, 0.0]
                }
            }
        },
        {"$project": {"_id": 0, "_user": 0}},
    ]
    cursor = db.withdrawal_requests.aggregate(pipeline)
    return await cursor.to_list(length=500)


async def get_withdrawal_stats() -> Dict[str, Any]:
    """Returns aggregate stats: pending count and total paid SYP."""
    db = await get_db()
    pending_count = await db.withdrawal_requests.count_documents({"status": "pending"})
    rejected_count = await db.withdrawal_requests.count_documents({"status": "rejected"})

    pipeline = [
        {"$match": {"status": "processed"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
    ]
    cursor = db.withdrawal_requests.aggregate(pipeline)
    result = await cursor.to_list(length=1)
    total_paid = result[0]["total"] if result else 0.0

    return {
        "pending_count": pending_count,
        "rejected_count": rejected_count,
        "total_paid_syp": round(total_paid, 2),
    }


async def mark_request_paid(
    request_id: str,
    processed_by: str,
    shamcash_ref: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Atomically marks a withdrawal request as processed.

    Returns the updated document (user_id + amount) for notification purposes.
    Raises ValueError if not found or already processed (idempotency guard).
    """
    db = await get_db()
    update: Dict[str, Any] = {
        "status": "processed",
        "processed_at": datetime.now(timezone.utc),
        "processed_by": processed_by,
    }
    if shamcash_ref:
        update["shamcash_ref"] = shamcash_ref.strip()

    result = await db.withdrawal_requests.find_one_and_update(
        {"request_id": request_id, "status": "pending"},
        {"$set": update},
        return_document=True,
    )
    if result is None:
        # Check if it exists at all (already processed vs truly missing)
        existing = await db.withdrawal_requests.find_one({"request_id": request_id})
        if existing is None:
            raise ValueError(f"Withdrawal request '{request_id}' not found")
        raise ValueError(
            f"Withdrawal request '{request_id}' is already '{existing['status']}'"
        )

    logger.info(
        "Withdrawal marked as paid",
        request_id=request_id,
        user_id=result["user_id"],
        amount=result["amount"],
        processed_by=processed_by,
    )
    return result


async def reject_request(
    request_id: str,
    processed_by: str,
) -> Dict[str, Any]:
    """
    Atomically marks a withdrawal request as rejected.
    The caller is responsible for restoring the user's balance.

    Returns the updated document (user_id + amount) for balance restoration and notification.
    Raises ValueError if not found or already processed.
    """
    db = await get_db()
    update = {
        "status": "rejected",
        "processed_at": datetime.now(timezone.utc),
        "processed_by": processed_by,
    }
    result = await db.withdrawal_requests.find_one_and_update(
        {"request_id": request_id, "status": "pending"},
        {"$set": update},
        return_document=True,
    )
    if result is None:
        existing = await db.withdrawal_requests.find_one({"request_id": request_id})
        if existing is None:
            raise ValueError(f"Withdrawal request '{request_id}' not found")
        raise ValueError(
            f"Withdrawal request '{request_id}' is already '{existing['status']}'"
        )

    # Restore the user's balance atomically
    await db.referral_users.update_one(
        {"user_id": result["user_id"]},
        {"$inc": {"balance": result["amount"]}},
    )
    logger.info(
        "Withdrawal rejected and balance restored",
        request_id=request_id,
        user_id=result["user_id"],
        amount=result["amount"],
        processed_by=processed_by,
    )
    return result
