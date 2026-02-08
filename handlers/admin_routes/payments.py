from aiogram import Router, F, types

from config import ADMIN_IDS
from database import (
    get_payment_by_id,
    get_project_by_id,
    update_payment_status,
    update_project_status,
)
from keyboards.callbacks import PaymentCallback
from utils.constants import (
    MSG_PAYMENT_CONFIRMED_ADMIN,
    MSG_PAYMENT_CONFIRMED_CLIENT,
    MSG_PAYMENT_REJECTED_ADMIN,
    STATUS_ACCEPTED,
    STATUS_OFFERED,
)
from utils.formatters import escape_md

router = Router()

@router.callback_query(PaymentCallback.filter(F.action == "view_receipt"), F.from_user.id.in_(ADMIN_IDS))
async def admin_view_receipt(
    callback: types.CallbackQuery, 
    bot,
    callback_data: PaymentCallback
):
    """Fetches and sends the actual receipt file for a specific payment."""
    payment_id = callback_data.id
    payment = await get_payment_by_id(payment_id)

    if not payment:
        await callback.answer("⚠️ File not found.", show_alert=True)
        return

    file_id = payment["file_id"]
    status = payment["status"]
    caption = f"📄 **Detail View: Payment #{payment_id}**\nStatus: {status}"

    try:
        await bot.send_document(
            callback.from_user.id, file_id, caption=caption, parse_mode="Markdown"
        )
        await callback.answer()
    except Exception:
        # Fallback if it's a photo ID that send_document doesn't like
        for admin_id in ADMIN_IDS:
             if admin_id == callback.from_user.id:
                  await bot.send_photo(admin_id, file_id, caption=caption, parse_mode="Markdown")
        await callback.answer()


@router.callback_query(PaymentCallback.filter(F.action == "confirm"), F.from_user.id.in_(ADMIN_IDS))
async def confirm_payment(
    callback: types.CallbackQuery, 
    bot,
    callback_data: PaymentCallback
):
    """Transitions project from 'Verification' to 'Accepted' (Ongoing)."""
    payment_id = callback_data.id

    # 1. Get Payment Info
    payment = await get_payment_by_id(payment_id)
    if not payment:
        await callback.answer("⚠️ Payment not found!", show_alert=True)
        return

    proj_id = payment["project_id"]

    # 2. Update Payment -> Accepted
    await update_payment_status(payment_id, "accepted")

    # 3. Update Project -> Accepted
    await update_project_status(proj_id, STATUS_ACCEPTED)

    res = await get_project_by_id(proj_id)
    if res:
        subject = escape_md(res["subject_name"])
        await bot.send_message(
            res["user_id"],
            MSG_PAYMENT_CONFIRMED_CLIENT.format(subject),
            parse_mode="Markdown",
        )

    await callback.message.edit_caption(
        caption=MSG_PAYMENT_CONFIRMED_ADMIN.format(proj_id)
        + f"\n(Payment #{payment_id} Accepted)",
        parse_mode="Markdown",
    )


@router.callback_query(PaymentCallback.filter(F.action == "reject"), F.from_user.id.in_(ADMIN_IDS))
async def reject_payment(
    callback: types.CallbackQuery, 
    bot,
    callback_data: PaymentCallback
):
    """Marks project as payment-failed and notifies the student."""
    payment_id = callback_data.id

    payment = await get_payment_by_id(payment_id)
    if not payment:
        return

    proj_id = payment["project_id"]

    # 1. Update Payment -> Rejected
    await update_payment_status(payment_id, "rejected")

    # 2. Update Project -> Offered (Reset so they can try again)
    # We do NOT kill the project. We let them re-upload.
    await update_project_status(proj_id, STATUS_OFFERED)

    res = await get_project_by_id(proj_id)
    if res:
        # Custom reject message telling them to try again
        await bot.send_message(
            res["user_id"],
            "❌ **تم رفض عملية الدفع.**\nالرجاء التأكد من الإيصال وإعادة المحاولة من قائمة 'عروضي'.",
            parse_mode="Markdown",
        )

    await callback.message.edit_caption(
        caption=MSG_PAYMENT_REJECTED_ADMIN.format(proj_id)
        + f"\n(Payment #{payment_id} Rejected)",
        parse_mode="Markdown",
    )
