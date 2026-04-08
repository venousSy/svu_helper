import logging
from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramAPIError

from application.project_service import (
    AddProjectService,
    GetOfferDetailService,
    GetStudentOffersService,
    GetStudentProjectsService,
    VerifyProjectOwnershipService,
)
from application.payment_service import SubmitPaymentService
from config import settings
from infrastructure.repositories import PaymentRepository, ProjectRepository
from keyboards.admin_kb import get_new_project_alert_kb, get_payment_verify_kb
from keyboards.client_kb import (
    get_cancel_payment_kb,
    get_offer_actions_kb,
    get_offers_list_kb,
)
from keyboards.callbacks import MenuCallback, ProjectCallback
from states import ProjectOrder
from utils.constants import (
    MSG_ASK_DEADLINE,
    MSG_ASK_DETAILS,
    MSG_ASK_SUBJECT,
    MSG_ASK_TUTOR,
    MSG_NO_DESC,
    BTN_NEW_PROJECT,
    BTN_MY_PROJECTS,
    BTN_MY_OFFERS,
    MSG_OFFER_ACCEPTED,
    MSG_OFFER_DETAILS,
    MSG_PROJECT_SUBMITTED,
    MSG_RECEIPT_RECEIVED,
)
from utils.formatters import (
    escape_md,
    format_admin_notification,
    format_offer_list,
    format_student_projects,
)
from utils.helpers import get_file_id, get_file_size
from middlewares.throttling import ThrottlingMiddleware

router = Router()
logger = logging.getLogger(__name__)
router.message.middleware(ThrottlingMiddleware(rate_limit=0.5))

MAX_FILE_SIZE_MB = AddProjectService.MAX_FILE_SIZE_MB
MAX_FILE_SIZE_BYTES = AddProjectService.MAX_FILE_SIZE_BYTES
ALLOWED_DOCUMENT_MIMES = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
]

# ── PROJECT SUBMISSION FSM ──────────────────────────────────────────────────

@router.callback_query(MenuCallback.filter(F.action == "new_project"))
async def cb_start_project(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(MSG_ASK_SUBJECT, parse_mode="Markdown")
    await state.set_state(ProjectOrder.subject)
    await callback.answer()


@router.message(F.text == BTN_NEW_PROJECT)
@router.message(Command("new_project"))
async def start_project(message: types.Message, state: FSMContext):
    await message.answer(MSG_ASK_SUBJECT, parse_mode="Markdown")
    await state.set_state(ProjectOrder.subject)


@router.message(ProjectOrder.subject, F.text)
async def process_subject(message: types.Message, state: FSMContext):
    if len(message.text) > AddProjectService.MAX_SUBJECT_LENGTH:
        return await message.answer(
            f"⚠️ اسم المادة طويل جداً. الحد الأقصى {AddProjectService.MAX_SUBJECT_LENGTH} حرف."
        )
    await state.update_data(subject=message.text)
    await message.answer(MSG_ASK_TUTOR, parse_mode="Markdown")
    await state.set_state(ProjectOrder.tutor)


@router.message(ProjectOrder.tutor, F.text)
async def process_tutor(message: types.Message, state: FSMContext):
    if len(message.text) > AddProjectService.MAX_TUTOR_LENGTH:
        return await message.answer(
            f"⚠️ اسم المدرس طويل جداً. الحد الأقصى {AddProjectService.MAX_TUTOR_LENGTH} حرف."
        )
    await state.update_data(tutor=message.text)
    await message.answer(MSG_ASK_DEADLINE, parse_mode="Markdown")
    await state.set_state(ProjectOrder.deadline)


@router.message(ProjectOrder.deadline, F.text)
async def process_deadline(message: types.Message, state: FSMContext):
    if len(message.text) > AddProjectService.MAX_DEADLINE_LENGTH:
        return await message.answer("⚠️ التاريخ طويل جداً. الرجاء الاختصار.")
    await state.update_data(deadline=message.text)
    await message.answer(MSG_ASK_DETAILS, parse_mode="Markdown")
    await state.set_state(ProjectOrder.details)


@router.message(ProjectOrder.subject)
@router.message(ProjectOrder.tutor)
@router.message(ProjectOrder.deadline)
async def reject_media_early(message: types.Message):
    await message.answer(
        "⚠️ الرجاء إدخال النص مطلوب أولاً. يمكنك رفع الملفات في الخطوة التالية."
    )


@router.message(ProjectOrder.details)
async def process_details(
    message: types.Message,
    state: FSMContext,
    bot,
    project_repo: ProjectRepository,
):
    file_size = get_file_size(message)
    if file_size and file_size > MAX_FILE_SIZE_BYTES:
        await message.answer(f"⚠️ حجم الملف كبير جداً. الحد الأقصى هو {MAX_FILE_SIZE_MB}MB.")
        return

    data = await state.get_data()
    file_id, file_type = get_file_id(message)
    details_text = message.text or message.caption or MSG_NO_DESC
    user = message.from_user

    try:
        project_id = await AddProjectService(project_repo).execute(
            user_id=user.id,
            username=user.username,
            user_full_name=user.full_name,
            subject=data["subject"],
            tutor=data["tutor"],
            deadline=data["deadline"],
            details=details_text,
            file_id=file_id,
            file_type=file_type,
        )
        await message.answer(
            MSG_PROJECT_SUBMITTED.format(project_id),
            parse_mode="Markdown",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        admin_text = format_admin_notification(
            project_id, data["subject"], data["deadline"], details_text,
            user_name=user.full_name, username=user.username,
        )
        for admin_id in settings.admin_ids:
            try:
                await bot.send_message(
                    admin_id, admin_text, parse_mode="Markdown",
                    reply_markup=get_new_project_alert_kb(project_id),
                )
            except TelegramAPIError as e:
                logger.error(f"Failed to notify admin {admin_id}: {e}")
        await state.clear()

    except ValueError as e:
        await message.answer(f"⚠️ {e}", reply_markup=types.ReplyKeyboardRemove())
        await state.clear()
    except Exception as e:
        logger.error(f"Failed to submit project: {e}", exc_info=True)
        await message.answer(
            "⚠️ حدث خطأ أثناء حفظ المشروع. حاول مرة أخرى لاحقاً.",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        await state.clear()


# ── OFFER ACCEPTANCE & PAYMENT ──────────────────────────────────────────────

@router.callback_query(ProjectCallback.filter(F.action == "accept"))
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


@router.callback_query(MenuCallback.filter(F.action == "cancel_pay"))
async def cancel_payment_process(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🚫 تم إلغاء عملية الدفع. يمكنك قبول العرض لاحقاً من قائمة 'عروضي'."
    )
    await callback.answer()


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
                logger.error(f"Failed to relay receipt {result.payment_id} to admin {admin_id}: {e}")
        await state.clear()

    except Exception as e:
        logger.error(f"Payment upload failed: {e}", exc_info=True)
        await message.answer("⚠️ حدث خطأ أثناء رفع الإيصال. حاول مرة أخرى.")
        await state.clear()


# ── PROJECT / OFFER VIEWS ───────────────────────────────────────────────────

@router.callback_query(MenuCallback.filter(F.action == "my_projects"))
async def cb_view_projects(
    callback: types.CallbackQuery, project_repo: ProjectRepository
):
    projects = await GetStudentProjectsService(project_repo).execute(callback.from_user.id)
    await callback.message.answer(format_student_projects(projects), parse_mode="Markdown")
    await callback.answer()


@router.message(F.text == BTN_MY_PROJECTS)
@router.message(Command("my_projects"))
async def view_projects(message: types.Message, project_repo: ProjectRepository):
    projects = await GetStudentProjectsService(project_repo).execute(message.from_user.id)
    await message.answer(format_student_projects(projects), parse_mode="Markdown")


@router.callback_query(MenuCallback.filter(F.action == "my_offers"))
async def cb_view_offers(
    callback: types.CallbackQuery, project_repo: ProjectRepository
):
    offers = await GetStudentOffersService(project_repo).execute(callback.from_user.id)
    await callback.message.answer(
        format_offer_list(offers), parse_mode="Markdown", reply_markup=get_offers_list_kb(offers)
    )
    await callback.answer()


@router.message(F.text == BTN_MY_OFFERS)
@router.message(Command("my_offers"))
async def view_offers(message: types.Message, project_repo: ProjectRepository):
    offers = await GetStudentOffersService(project_repo).execute(message.from_user.id)
    await message.answer(
        format_offer_list(offers), parse_mode="Markdown", reply_markup=get_offers_list_kb(offers)
    )


@router.callback_query(ProjectCallback.filter(F.action == "view_offer"))
async def show_specific_offer(
    callback: types.CallbackQuery,
    callback_data: ProjectCallback,
    project_repo: ProjectRepository,
):
    proj_id = callback_data.id
    try:
        res = await GetOfferDetailService(project_repo).execute(proj_id, callback.from_user.id)
    except PermissionError as e:
        return await callback.answer(f"⚠️ {e}", show_alert=True)

    subject = escape_md(res["subject_name"])
    price = escape_md(res["price"])
    delivery = escape_md(res["delivery_date"])
    text = MSG_OFFER_DETAILS.format(subject, price, delivery, escape_md(proj_id))
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=get_offer_actions_kb(proj_id))
