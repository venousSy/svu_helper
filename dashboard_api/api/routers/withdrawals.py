"""
Dashboard Withdrawals Router
=============================
Endpoints for viewing and managing student referral withdrawal requests.
Sends Telegram notifications directly via Bot API (no bot process dependency).
"""
import structlog
import aiohttp
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from config import settings
from dashboard_api.api.dependencies import get_current_user
from dashboard_api.repositories.withdrawals_repo import (
    get_all_requests,
    get_withdrawal_stats,
    mark_request_paid,
    reject_request,
)

logger = structlog.get_logger(__name__)

router = APIRouter(
    prefix="/api/withdrawals",
    tags=["withdrawals"],
    dependencies=[Depends(get_current_user)],
)


# ── Schemas ──────────────────────────────────────────────────────────────────

class MarkPaidRequest(BaseModel):
    shamcash_ref: Optional[str] = None


# ── Telegram helper ───────────────────────────────────────────────────────────

async def _send_telegram(user_id: int, text: str) -> None:
    """Fire-and-forget Telegram message sent directly via Bot API."""
    url = f"https://api.telegram.org/bot{settings.BOT_TOKEN}/sendMessage"
    payload = {"chat_id": user_id, "text": text, "parse_mode": "Markdown"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    logger.warning("Telegram send failed", user_id=user_id, status=resp.status, body=body)
    except Exception as exc:
        logger.warning("Telegram send exception", user_id=user_id, error=str(exc))


def _build_paid_message(amount: float, shamcash_ref: Optional[str]) -> str:
    ref_line = f"\nرقم العملية: `{shamcash_ref}`" if shamcash_ref else ""
    return (
        f"✅ تم تحويل *{amount:.0f} ل.س* إلى حساب ShamCash الخاص بك.{ref_line}\n"
        f"تحقق من تطبيق ShamCash."
    )


def _build_rejected_message(amount: float) -> str:
    return (
        f"❌ عذراً، تعذّر معالجة طلب سحبك.\n"
        f"تمت إعادة *{amount:.0f} ل.س* إلى رصيدك تلقائياً."
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/stats")
async def withdrawals_stats():
    """Pending count + total paid SYP for sidebar badge and stat cards."""
    return await get_withdrawal_stats()


@router.get("")
async def list_withdrawals(status: Optional[str] = None):
    """
    List all withdrawal requests, joined with current user balance.
    Query param: ?status=pending|processed|rejected (omit for all)
    """
    return await get_all_requests(status_filter=status)


@router.post("/{request_id}/mark-paid", status_code=status.HTTP_200_OK)
async def mark_paid(
    request_id: str,
    body: MarkPaidRequest,
    current_user: str = Depends(get_current_user),
):
    """
    Mark a pending withdrawal as processed.
    Returns HTTP 409 if already processed/rejected (idempotency guard).
    Sends a Telegram notification to the student after updating the DB.
    """
    try:
        doc = await mark_request_paid(
            request_id=request_id,
            processed_by=current_user,
            shamcash_ref=body.shamcash_ref,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    # Notify student (fire-and-forget)
    await _send_telegram(
        doc["user_id"],
        _build_paid_message(doc["amount"], body.shamcash_ref),
    )

    # Broadcast live update to dashboard WebSocket clients
    try:
        from dashboard_api.api.routers.ws import manager
        await manager.broadcast({
            "type": "withdrawal_updated",
            "id": request_id,
            "status": "processed",
        })
    except Exception as exc:
        logger.warning("WS broadcast failed", error=str(exc))

    logger.info("Withdrawal marked paid via dashboard", request_id=request_id, by=current_user)
    return {"ok": True, "request_id": request_id, "status": "processed"}


@router.post("/{request_id}/reject", status_code=status.HTTP_200_OK)
async def reject(
    request_id: str,
    current_user: str = Depends(get_current_user),
):
    """
    Reject a pending withdrawal request and atomically restore the user's balance.
    Returns HTTP 409 if already processed/rejected.
    Sends a Telegram notification to the student.
    """
    try:
        doc = await reject_request(
            request_id=request_id,
            processed_by=current_user,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    await _send_telegram(
        doc["user_id"],
        _build_rejected_message(doc["amount"]),
    )

    try:
        from dashboard_api.api.routers.ws import manager
        await manager.broadcast({
            "type": "withdrawal_updated",
            "id": request_id,
            "status": "rejected",
        })
    except Exception as exc:
        logger.warning("WS broadcast failed", error=str(exc))

    logger.info("Withdrawal rejected via dashboard", request_id=request_id, by=current_user)
    return {"ok": True, "request_id": request_id, "status": "rejected"}
