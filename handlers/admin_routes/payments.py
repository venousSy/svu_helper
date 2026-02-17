from aiogram import Router, F, types
import logging

from config import settings
from database.repositories import ProjectRepository, PaymentRepository
from keyboards.callbacks import PaymentCallback
from utils.constants import (
    MSG_PAYMENT_CONFIRMED_ADMIN,
    MSG_PAYMENT_CONFIRMED_CLIENT,
    MSG_PAYMENT_REJECTED_ADMIN,
)
from utils.enums import ProjectStatus, PaymentStatus
from utils.formatters import escape_md

router = Router()
logger = logging.getLogger(__name__)

@router.callback_query(PaymentCallback.filter(F.action == "view_receipt"), F.from_user.id.in_(settings.ADMIN_IDS))
async def admin_view_receipt(
    callback: types.CallbackQuery, 
    bot,
    callback_data: PaymentCallback
):
    """Fetches and sends the actual receipt file for a specific payment."""
    payment_id = callback_data.id
    payment = await PaymentRepository.get_payment(payment_id)

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
    except Exception as e:
        logger.warning(f"Failed to send document for payment {payment_id}: {e}")
        # Fallback if it's a photo ID that send_document doesn't like
        for admin_id in settings.ADMIN_IDS:
             if admin_id == callback.from_user.id:
                  await bot.send_photo(admin_id, file_id, caption=caption, parse_mode="Markdown")
        await callback.answer()


@router.callback_query(PaymentCallback.filter(F.action == "confirm"), F.from_user.id.in_(settings.ADMIN_IDS))
async def confirm_payment(
    callback: types.CallbackQuery, 
    bot,
    callback_data: PaymentCallback
):
    """Transitions project from 'Verification' to 'Accepted' (Ongoing)."""
    payment_id = callback_data.id

    # 1. Get Payment Info
    payment = await PaymentRepository.get_payment(payment_id)
    if not payment:
        await callback.answer("⚠️ Payment not found!", show_alert=True)
        return

    proj_id = payment["project_id"]

    # 2. Update Payment -> Accepted
    await PaymentRepository.update_status(payment_id, PaymentStatus.ACCEPTED)

    # 3. Update Project -> Accepted
    await ProjectRepository.update_status(proj_id, ProjectStatus.ACCEPTED)

    res = await ProjectRepository.get_project_by_id(proj_id)
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


@router.callback_query(PaymentCallback.filter(F.action == "reject"), F.from_user.id.in_(settings.ADMIN_IDS))
async def reject_payment(
    callback: types.CallbackQuery, 
    bot,
    callback_data: PaymentCallback
):
    """Marks project as payment-failed and notifies the student."""
    payment_id = callback_data.id

    payment = await PaymentRepository.get_payment(payment_id)
    if not payment:
        return

    proj_id = payment["project_id"]

    # 1. Update Payment -> Rejected
    await PaymentRepository.update_status(payment_id, PaymentStatus.REJECTED)

    # 2. Update Project -> Offered (Reset so they can try again)
    # We do NOT kill the project. We let them re-upload.
    await ProjectRepository.update_status(proj_id, ProjectStatus.OFFERED)

    res = await ProjectRepository.get_project_by_id(proj_id)
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
