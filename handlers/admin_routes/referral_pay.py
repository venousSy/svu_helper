"""
Admin Referral Pay Handler
===========================
Provides admin-only bot commands to manually mark withdrawal requests as paid or rejected.

Commands:
  /pay <request_id> [shamcash_ref]   — mark a pending withdrawal as processed
  /rejectpay <request_id>            — reject a pending withdrawal and restore balance
"""
import structlog
from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject

from config import settings
from utils.constants import MSG_WITHDRAWAL_PAID, MSG_WITHDRAWAL_REJECTED_ADMIN

logger = structlog.get_logger(__name__)
router = Router()


def _build_paid_msg(amount: float, shamcash_ref: str | None) -> str:
    ref_line = f"\nرقم العملية: `{shamcash_ref}`" if shamcash_ref else ""
    return MSG_WITHDRAWAL_PAID.format(amount=amount, ref_line=ref_line)


@router.message(Command("pay"), F.from_user.id.in_(settings.admin_ids))
async def cmd_pay(
    message: types.Message,
    command: CommandObject,
    user_referral_repo,
    bot,
) -> None:
    """
    /pay <request_id> [shamcash_ref]

    Marks a pending withdrawal as processed and notifies the student.
    """
    if not command.args:
        await message.reply(
            "⚠️ الاستخدام: `/pay <request_id> [shamcash_ref]`\n\n"
            "مثال: `/pay abc-123 TXN-456`",
            parse_mode="Markdown",
        )
        return

    parts = command.args.strip().split(maxsplit=1)
    request_id = parts[0]
    shamcash_ref = parts[1] if len(parts) > 1 else None

    try:
        doc = await user_referral_repo.mark_withdrawal_paid(
            request_id=request_id,
            processed_by="admin_bot",
            shamcash_ref=shamcash_ref,
        )
    except ValueError as exc:
        await message.reply(f"❌ {exc}")
        return

    # Notify the student
    user_msg = _build_paid_msg(doc["amount"], shamcash_ref)
    try:
        await bot.send_message(doc["user_id"], user_msg, parse_mode="Markdown")
    except Exception as exc:
        logger.warning(
            "Could not notify student of payment",
            user_id=doc["user_id"],
            request_id=request_id,
            error=str(exc),
        )
        await message.reply(
            f"✅ تم تحديث الطلب `{request_id}` كمدفوع.\n"
            f"⚠️ لم يتمكن البوت من إرسال إشعار للمستخدم ({doc['user_id']}).",
            parse_mode="Markdown",
        )
        return

    ref_display = f" (ref: `{shamcash_ref}`)" if shamcash_ref else ""
    await message.reply(
        f"✅ الطلب `{request_id}` مُعالَج.\n"
        f"💰 المبلغ: *{doc['amount']:.0f} ل.س*{ref_display}\n"
        f"📲 تمّ إشعار المستخدم {doc['user_id']}.",
        parse_mode="Markdown",
    )
    logger.info(
        "Withdrawal marked paid via /pay command",
        request_id=request_id,
        user_id=doc["user_id"],
        admin_id=message.from_user.id,
        shamcash_ref=shamcash_ref,
    )


@router.message(Command("rejectpay"), F.from_user.id.in_(settings.admin_ids))
async def cmd_rejectpay(
    message: types.Message,
    command: CommandObject,
    user_referral_repo,
    bot,
) -> None:
    """
    /rejectpay <request_id>

    Rejects a pending withdrawal, restores the user's balance, and notifies them.
    """
    if not command.args:
        await message.reply(
            "⚠️ الاستخدام: `/rejectpay <request_id>`\n\n"
            "مثال: `/rejectpay abc-123`",
            parse_mode="Markdown",
        )
        return

    request_id = command.args.strip().split()[0]

    try:
        doc = await user_referral_repo.reject_withdrawal(
            request_id=request_id,
            processed_by="admin_bot",
        )
    except ValueError as exc:
        await message.reply(f"❌ {exc}")
        return

    # Restore the user's balance
    await user_referral_repo.restore_balance(doc["user_id"], doc["amount"])

    # Notify the student
    user_msg = MSG_WITHDRAWAL_REJECTED_ADMIN.format(amount=doc["amount"])
    try:
        await bot.send_message(doc["user_id"], user_msg, parse_mode="Markdown")
    except Exception as exc:
        logger.warning(
            "Could not notify student of rejection",
            user_id=doc["user_id"],
            request_id=request_id,
            error=str(exc),
        )

    await message.reply(
        f"✅ الطلب `{request_id}` مرفوض.\n"
        f"💰 تمت إعادة *{doc['amount']:.0f} ل.س* إلى رصيد المستخدم {doc['user_id']}.\n"
        f"📲 تمّ إشعار المستخدم.",
        parse_mode="Markdown",
    )
    logger.info(
        "Withdrawal rejected via /rejectpay command",
        request_id=request_id,
        user_id=doc["user_id"],
        admin_id=message.from_user.id,
    )
