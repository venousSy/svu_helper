import structlog
from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramAPIError

from application.project_service import VerifyProjectOwnershipService
from application.payment_service import SubmitPaymentService
from application.audit_service import AuditService
from domain.enums import AuditEventType
from config import settings
from infrastructure.repositories import PaymentRepository, ProjectRepository, AuditRepository
from keyboards.callbacks import MenuCallback, ProjectCallback, ProjectAction, MenuAction
from keyboards.factory import KeyboardFactory
from states import ProjectOrder
from utils.constants import (
    MSG_CANCEL_DONE,
    MSG_FILE_TOO_LARGE,
    MSG_NEW_PAYMENT_ADMIN_ALERT,
    MSG_OFFER_ACCEPTED,
    MSG_PAYMENT_DOC_INVALID,
    MSG_PAYMENT_UPLOAD_ERROR,
    MSG_RECEIPT_RECEIVED,
    MSG_PAYMENT_CANCELLED,
    MSG_PAYMENT_PROOF_HINT,
)
from utils.helpers import get_file_id

router = Router()
logger = structlog.get_logger(__name__)

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
    audit_repo: AuditRepository,
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
        reply_markup=KeyboardFactory.cancel_payment(),
    )
    
    await AuditService(audit_repo).log_event(
        user_id=callback.from_user.id,
        role="student",
        event_type=AuditEventType.OFFER_ACCEPTED,
        entity_id=proj_id,
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
    await callback.answer(MSG_CANCEL_DONE)


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
    audit_repo: AuditRepository,
):
    """Student sends receipt – SubmitPaymentService persists it, handler sends notifications."""
    if message.document:
        if message.document.file_size > MAX_FILE_SIZE_BYTES:
            await message.answer(MSG_FILE_TOO_LARGE.format(MAX_FILE_SIZE_MB))
            return
        if (
            message.document.mime_type not in ALLOWED_DOCUMENT_MIMES
            and "image" not in message.document.mime_type
        ):
            await message.answer(MSG_PAYMENT_DOC_INVALID)
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
                    MSG_NEW_PAYMENT_ADMIN_ALERT.format(result.payment_id, result.proj_id),
                    parse_mode="Markdown",
                )
                if result.file_type == "photo":
                    await bot.send_photo(
                        admin_id, result.file_id,
                        caption=f"verify_pay_{result.payment_id}",
                        reply_markup=KeyboardFactory.payment_verify(result.payment_id),
                    )
                else:
                    await bot.send_document(
                        admin_id, result.file_id,
                        caption=f"verify_pay_{result.payment_id}",
                        reply_markup=KeyboardFactory.payment_verify(result.payment_id),
                    )
            except TelegramAPIError as e:
                logger.error("Failed to relay receipt to admin", payment_id=result.payment_id, admin_id=admin_id, error=str(e))
                
        await AuditService(audit_repo).log_event(
            user_id=message.from_user.id,
            role="student",
            event_type=AuditEventType.PAYMENT_SUBMITTED,
            entity_id=result.payment_id,
            metadata={"project_id": result.proj_id}
        )
        
        await state.clear()

    except Exception as e:
        logger.error("Payment upload failed", error=str(e), exc_info=True)
        await message.answer(MSG_PAYMENT_UPLOAD_ERROR)
        await state.clear()
