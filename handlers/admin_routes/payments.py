import logging
from aiogram import Router, F, types

from application.payment_service import ConfirmPaymentService, RejectPaymentService
from config import settings
from infrastructure.repositories import PaymentRepository, ProjectRepository
from keyboards.callbacks import PaymentCallback
from utils.constants import (
    MSG_PAYMENT_CONFIRMED_ADMIN,
    MSG_PAYMENT_CONFIRMED_CLIENT,
    MSG_PAYMENT_REJECTED_ADMIN,
)
from utils.formatters import escape_md

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(
    PaymentCallback.filter(F.action == "view_receipt"),
    F.from_user.id.in_(settings.admin_ids),
)
async def admin_view_receipt(
    callback: types.CallbackQuery,
    bot,
    callback_data: PaymentCallback,
    payment_repo: PaymentRepository,
):
    """Fetches and sends the actual receipt file for a specific payment."""
    payment_id = callback_data.id
    payment = await payment_repo.get_payment(payment_id)
    if not payment:
        return await callback.answer("⚠️ File not found.", show_alert=True)

    file_id = payment["file_id"]
    status = payment["status"]
    caption = f"📄 **Detail View: Payment #{payment_id}**\nStatus: {status}"
    try:
        await bot.send_document(callback.from_user.id, file_id, caption=caption, parse_mode="Markdown")
        await callback.answer()
    except Exception as e:
        logger.warning(f"Failed to send document for payment {payment_id}: {e}")
        try:
            await bot.send_photo(callback.from_user.id, file_id, caption=caption, parse_mode="Markdown")
        except Exception:
            pass
        await callback.answer()


@router.callback_query(
    PaymentCallback.filter(F.action == "confirm"),
    F.from_user.id.in_(settings.admin_ids),
)
async def confirm_payment(
    callback: types.CallbackQuery,
    bot,
    callback_data: PaymentCallback,
    payment_repo: PaymentRepository,
    project_repo: ProjectRepository,
):
    """ConfirmPaymentService does the DB work; handler sends notifications."""
    payment_id = callback_data.id
    try:
        result = await ConfirmPaymentService(project_repo, payment_repo).execute(payment_id)
    except ValueError as e:
        return await callback.answer(f"⚠️ {e}", show_alert=True)

    await bot.send_message(
        result.user_id,
        MSG_PAYMENT_CONFIRMED_CLIENT.format(escape_md(result.subject)),
        parse_mode="Markdown",
    )
    await callback.message.edit_caption(
        caption=MSG_PAYMENT_CONFIRMED_ADMIN.format(result.proj_id)
        + f"\n(Payment #{result.payment_id} Accepted)",
        parse_mode="Markdown",
    )


@router.callback_query(
    PaymentCallback.filter(F.action == "reject"),
    F.from_user.id.in_(settings.admin_ids),
)
async def reject_payment(
    callback: types.CallbackQuery,
    bot,
    callback_data: PaymentCallback,
    payment_repo: PaymentRepository,
    project_repo: ProjectRepository,
):
    """RejectPaymentService resets the project; handler notifies the student."""
    payment_id = callback_data.id
    try:
        result = await RejectPaymentService(project_repo, payment_repo).execute(payment_id)
    except ValueError as e:
        return await callback.answer(f"⚠️ {e}", show_alert=True)

    if result.user_id:
        await bot.send_message(
            result.user_id,
            "❌ **تم رفض عملية الدفع.**\nالرجاء التأكد من الإيصال وإعادة المحاولة من قائمة 'عروضي'.",
            parse_mode="Markdown",
        )
    await callback.message.edit_caption(
        caption=MSG_PAYMENT_REJECTED_ADMIN.format(result.proj_id)
        + f"\n(Payment #{result.payment_id} Rejected)",
        parse_mode="Markdown",
    )
