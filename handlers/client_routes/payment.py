import logging
from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramAPIError

from application.project_service import VerifyProjectOwnershipService
from application.payment_service import SubmitPaymentService
from config import settings
from infrastructure.repositories import PaymentRepository, ProjectRepository
from keyboards.admin_kb import get_payment_verify_kb
from keyboards.client_kb import get_cancel_payment_kb
from keyboards.callbacks import MenuCallback, ProjectCallback, ProjectAction, MenuAction
from states import ProjectOrder
from utils.constants import MSG_OFFER_ACCEPTED, MSG_RECEIPT_RECEIVED, MSG_PAYMENT_CANCELLED, MSG_PAYMENT_PROOF_HINT
from utils.helpers import get_file_id

router = Router()
logger = logging.getLogger(__name__)

MAX_FILE_SIZE_MB = 20
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_DOCUMENT_MIMES = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
]

# ── OFFER ACCEPTANCE & PAYMENT ──────────────────────────────────────────────

@router.callback_query(ProjectCallback.filter(F.action == ProjectAction.accept))
async def student_accept_offer(
    callback: types.CallbackQuery,
    state: FSMContext,
    callback_data: ProjectCallback,
    project_repo: ProjectRepository,
):
    """Student accepts an offer – validates ownership then enters payment FSM."""
    proj_id = callback_data.id
    try:
        await VerifyProjectOwnershipService(project_repo).execute(proj_id, callback.from_user.id)
    except PermissionError as e:
        return await callback.answer(f"⚠️ {e}", show_alert=True)

    await state.update_data(active_pay_proj_id=proj_id)
    await callback.message.edit_text(
        MSG_OFFER_ACCEPTED.format(proj_id),
        parse_mode="Markdown",
        reply_markup=get_cancel_payment_kb(),
    )
    await state.set_state(ProjectOrder.waiting_for_payment_proof)
    await callback.answer()


@router.callback_query(MenuCallback.filter(F.action == MenuAction.cancel_pay))
async def cancel_payment_process(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        MSG_PAYMENT_CANCELLED,
        parse_mode="Markdown"
    )
    await callback.answer("تم الإلغاء ✓")


@router.message(ProjectOrder.waiting_for_payment_proof, F.text)
async def process_payment_proof_invalid(message: types.Message):
    await message.answer(MSG_PAYMENT_PROOF_HINT)


@router.message(ProjectOrder.waiting_for_payment_proof, F.photo | F.document)
async def process_payment_proof(
    message: types.Message,
    state: FSMContext,
    bot,
    project_repo: ProjectRepository,
    payment_repo: PaymentRepository,
):
    """Student sends receipt – SubmitPaymentService persists it, handler sends notifications."""
    if message.document:
        if message.document.file_size > MAX_FILE_SIZE_BYTES:
            await message.answer(f"⚠️ حجم الملف كبير جداً. الحد الأقصى هو {MAX_FILE_SIZE_MB}MB.")
            return
        if (
            message.document.mime_type not in ALLOWED_DOCUMENT_MIMES
            and "image" not in message.document.mime_type
        ):
            await message.answer("⚠️ الرجاء رفع صورة أو ملف PDF/Word كإثبات للدفع.")
            return

    data = await state.get_data()
    file_id, file_type = get_file_id(message)

    try:
        result = await SubmitPaymentService(project_repo, payment_repo).execute(
            proj_id=data.get("active_pay_proj_id"),
            user_id=message.from_user.id,
            file_id=file_id,
            file_type=file_type,
        )
        await message.answer(MSG_RECEIPT_RECEIVED, parse_mode="Markdown")

        for admin_id in settings.admin_ids:
            try:
                await bot.send_message(
                    admin_id,
                    f"💰 **إيصال دفع جديد (رقم #{result.payment_id})**\nللمشروع: #{result.proj_id}",
                    parse_mode="Markdown",
                )
                if result.file_type == "photo":
                    await bot.send_photo(
                        admin_id, result.file_id,
                        caption=f"verify_pay_{result.payment_id}",
                        reply_markup=get_payment_verify_kb(result.payment_id),
                    )
                else:
                    await bot.send_document(
                        admin_id, result.file_id,
                        caption=f"verify_pay_{result.payment_id}",
                        reply_markup=get_payment_verify_kb(result.payment_id),
                    )
            except TelegramAPIError as e:
                logger.error("Failed to relay receipt to admin", payment_id=result.payment_id, admin_id=admin_id, error=str(e))
        await state.clear()

    except Exception as e:
        logger.error("Payment upload failed", error=str(e), exc_info=True)
        await message.answer("⚠️ حدث خطأ أثناء رفع الإيصال. حاول مرة أخرى.")
        await state.clear()
