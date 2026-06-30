"""
Dashboard Referrals Repository
================================
Provides aggregated and raw referral data for the admin dashboard.
Reads from `referral_users` and `commission_logs` MongoDB collections.
"""
from typing import Any, Dict, List

from infrastructure.mongo_db import get_db


async def get_all_referral_users() -> List[Dict[str, Any]]:
    """Returns all referral user records, sorted newest first."""
    db = await get_db()
    cursor = db.referral_users.find(
        {},
        {
            "user_id": 1,
            "referred_by": 1,
            "balance": 1,
            "last_withdrawal_date": 1,
            "created_at": 1,
        },
    ).sort("created_at", -1)
    return await cursor.to_list(length=500)


async def get_referral_tree() -> List[Dict[str, Any]]:
    """
    Returns each referrer with a list of the users they referred and
    the total commission they have earned.

    Shape:
        [
          {
            referrer_id: int,
            total_earned: float,
            current_balance: float,
            referral_count: int,
            referrals: [
              { user_id, joined_at, commissions: [{ project_id, amount, earned_at }] }
            ]
          },
          ...
        ]
    """
    db = await get_db()

    # 1. All users who were referred by someone
    cursor = db.referral_users.find(
        {"referred_by": {"$exists": True, "$ne": None}},
        {"user_id": 1, "referred_by": 1, "created_at": 1},
    )
    referred_docs = await cursor.to_list(length=None)

    # 2. All commission logs
    logs_cursor = db.commission_logs.find({})
    all_logs = await logs_cursor.to_list(length=None)

    # 3. All referrers' balance info
    referrer_ids = {d["referred_by"] for d in referred_docs}
    balance_cursor = db.referral_users.find(
        {"user_id": {"$in": list(referrer_ids)}},
        {"user_id": 1, "balance": 1},
    )
    balance_docs = await balance_cursor.to_list(length=None)
    balances: Dict[int, float] = {d["user_id"]: d.get("balance", 0.0) for d in balance_docs}

    # 4. Build log index: referred_user_id -> list of log entries
    logs_by_referral: Dict[int, list] = {}
    earned_by_referrer: Dict[int, float] = {}
    for log in all_logs:
        rid = log.get("referred_user_id")
        ref = log.get("referrer_id")
        if rid is not None:
            logs_by_referral.setdefault(rid, []).append({
                "project_id": log.get("project_id"),
                "project_subject": log.get("project_subject", ""),
                "amount": log.get("commission_amount", 0.0),
                "earned_at": log.get("earned_at"),
            })
        if ref is not None:
            earned_by_referrer[ref] = earned_by_referrer.get(ref, 0.0) + log.get("commission_amount", 0.0)

    # 5. Group referred users by referrer
    tree: Dict[int, dict] = {}
    for doc in referred_docs:
        referrer_id = doc["referred_by"]
        if referrer_id not in tree:
            tree[referrer_id] = {
                "referrer_id": referrer_id,
                "current_balance": balances.get(referrer_id, 0.0),
                "total_earned": round(earned_by_referrer.get(referrer_id, 0.0), 2),
                "referral_count": 0,
                "referrals": [],
            }
        uid = doc["user_id"]
        tree[referrer_id]["referrals"].append({
            "user_id": uid,
            "joined_at": doc.get("created_at"),
            "commissions": logs_by_referral.get(uid, []),
        })
        tree[referrer_id]["referral_count"] += 1

    # Sort by referral count descending
    return sorted(tree.values(), key=lambda x: x["referral_count"], reverse=True)


async def get_referral_summary() -> Dict[str, Any]:
    """Top-level numbers for the referral stats cards."""
    db = await get_db()

    total_referrers = await db.referral_users.count_documents(
        {"referred_by": {"$exists": True, "$ne": None}}
    )
    total_referred = await db.referral_users.count_documents(
        {"referred_by": {"$exists": True, "$ne": None}}
    )

    pipeline = [{"$group": {"_id": None, "total": {"$sum": "$commission_amount"}}}]
    cursor = db.commission_logs.aggregate(pipeline)
    result = await cursor.to_list(length=1)
    total_commissions_paid = result[0]["total"] if result else 0.0

    total_referrers_count = await db.referral_users.count_documents(
        {"referred_by": {"$exists": True, "$ne": None}}
    )
    # Count unique referrers
    unique_referrers = await db.referral_users.distinct("referred_by")
    unique_referrers_count = len([r for r in unique_referrers if r is not None])

    return {
        "total_referred_users": total_referred,
        "unique_referrers": unique_referrers_count,
        "total_commissions_paid": round(total_commissions_paid, 2),
    }
