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
from keyboards.callbacks import MenuCallback, PageCallback, ProjectCallback, ProjectAction, PageAction, MenuAction
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
from utils.pagination import build_nav_keyboard
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

@router.callback_query(MenuCallback.filter(F.action == MenuAction.new_project))
async def cb_start_project(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(MSG_ASK_SUBJECT, parse_mode="Markdown")
    await state.set_state(ProjectOrder.subject)
    await callback.answer()


@router.message(F.text == BTN_NEW_PROJECT)
@router.message(Command("new_project"))
async def start_project(message: types.Message, state: FSMContext):
    await message.answer(MSG_ASK_SUBJECT, parse_mode="Markdown")
    await state.set_state(ProjectOrder.subject)


@router.message(ProjectOrder.subject, F.text, ~F.text.startswith('/'))
async def process_subject(message: types.Message, state: FSMContext):
    if len(message.text) > AddProjectService.MAX_SUBJECT_LENGTH:
        return await message.answer(
            f"⚠️ اسم المادة طويل جداً. الحد الأقصى {AddProjectService.MAX_SUBJECT_LENGTH} حرف."
        )
    await state.update_data(subject=message.text)
    await message.answer(MSG_ASK_TUTOR, parse_mode="Markdown")
    await state.set_state(ProjectOrder.tutor)


@router.message(ProjectOrder.tutor, F.text, ~F.text.startswith('/'))
async def process_tutor(message: types.Message, state: FSMContext):
    if len(message.text) > AddProjectService.MAX_TUTOR_LENGTH:
        return await message.answer(
            f"⚠️ اسم المدرس طويل جداً. الحد الأقصى {AddProjectService.MAX_TUTOR_LENGTH} حرف."
        )
    await state.update_data(tutor=message.text)
    await message.answer(MSG_ASK_DEADLINE, parse_mode="Markdown")
    await state.set_state(ProjectOrder.deadline)


@router.message(ProjectOrder.deadline, F.text, ~F.text.startswith('/'))
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
                logger.error("Failed to notify admin", admin_id=admin_id, error=str(e))
        await state.clear()

    except ValueError as e:
        await message.answer(f"⚠️ {e}", reply_markup=types.ReplyKeyboardRemove())
        await state.clear()
    except Exception as e:
        logger.error("Failed to submit project", error=str(e), exc_info=True)
        await message.answer(
            "⚠️ حدث خطأ أثناء حفظ المشروع. حاول مرة أخرى لاحقاً.",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        await state.clear()


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
                logger.error("Failed to relay receipt to admin", payment_id=result.payment_id, admin_id=admin_id, error=str(e))
        await state.clear()

    except Exception as e:
        logger.error("Payment upload failed", error=str(e), exc_info=True)
        await message.answer("⚠️ حدث خطأ أثناء رفع الإيصال. حاول مرة أخرى.")
        await state.clear()


# ── PROJECT / OFFER VIEWS ───────────────────────────────────────────────────

@router.callback_query(MenuCallback.filter(F.action == MenuAction.my_projects))
async def cb_view_projects(
    callback: types.CallbackQuery, project_repo: ProjectRepository
):
    await _render_my_projects(callback, project_repo, page=0)


async def _render_my_projects(
    callback: types.CallbackQuery, project_repo: ProjectRepository, page: int
) -> None:
    from application.project_service import GetStudentProjectsService
    projects = await GetStudentProjectsService(project_repo).execute(callback.from_user.id)
    text, total_pages = format_student_projects(projects, page=page)
    kb = build_nav_keyboard(
        action="my_projects", page=page, total_pages=total_pages, back_action=MenuAction.close_list
    )
    
    try:
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    except Exception:
        pass
    await callback.answer()


@router.callback_query(PageCallback.filter(F.action == PageAction.my_projects))
async def cb_my_projects_page(
    callback: types.CallbackQuery,
    callback_data: PageCallback,
    project_repo: ProjectRepository,
):
    await _render_my_projects(callback, project_repo, page=callback_data.page)


@router.message(F.text == BTN_MY_PROJECTS)
@router.message(Command("my_projects"))
async def view_projects(message: types.Message, project_repo: ProjectRepository):
    projects = await GetStudentProjectsService(project_repo).execute(message.from_user.id)
    text, total_pages = format_student_projects(projects)
    kb = build_nav_keyboard(
        action="my_projects", page=0, total_pages=total_pages, back_action=MenuAction.close_list
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=kb)


@router.callback_query(MenuCallback.filter(F.action == MenuAction.my_offers))
async def cb_view_offers(
    callback: types.CallbackQuery, project_repo: ProjectRepository
):
    await _render_my_offers(callback, project_repo, page=0)


def _build_offers_kb(slice_, page: int, total_pages: int):
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from keyboards.callbacks import PageCallback as PC, MenuCallback as MC, MenuAction
    from keyboards.client_kb import get_offers_list_kb
    from aiogram import types
    builder = InlineKeyboardBuilder()
    item_kb = get_offers_list_kb(slice_)
    for row in item_kb.inline_keyboard:
        builder.row(*row)
    
    if total_pages > 1:
        nav = []
        if page > 0:
            nav.append(types.InlineKeyboardButton(
                text="⬅️ السابق",
                callback_data=PC(action="my_offers", page=page - 1).pack(),
            ))
        nav.append(types.InlineKeyboardButton(
            text=f"📄 {page + 1}/{total_pages}", callback_data="noop"
        ))
        if page < total_pages - 1:
            nav.append(types.InlineKeyboardButton(
                text="التالي ➡️",
                callback_data=PC(action="my_offers", page=page + 1).pack(),
            ))
        builder.row(*nav)
        
    builder.row(types.InlineKeyboardButton(
        text="⬅️ رجوع",
        callback_data=MC(action=MenuAction.close_list).pack(),
    ))
    return builder.as_markup()


async def _render_my_offers(
    callback: types.CallbackQuery, project_repo: ProjectRepository, page: int
) -> None:
    from application.project_service import GetStudentOffersService
    from utils.pagination import paginate
    offers = await GetStudentOffersService(project_repo).execute(callback.from_user.id)
    text, total_pages = format_offer_list(offers, page=page)
    slice_, _, _ = paginate(offers, page)
    item_kb = _build_offers_kb(slice_, page, total_pages)
        
    try:
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=item_kb)
    except Exception:
        pass
    await callback.answer()


@router.callback_query(PageCallback.filter(F.action == PageAction.my_offers))
async def cb_my_offers_page(
    callback: types.CallbackQuery,
    callback_data: PageCallback,
    project_repo: ProjectRepository,
):
    await _render_my_offers(callback, project_repo, page=callback_data.page)


@router.message(F.text == BTN_MY_OFFERS)
@router.message(Command("my_offers"))
async def view_offers(message: types.Message, project_repo: ProjectRepository):
    from application.project_service import GetStudentOffersService
    from utils.pagination import paginate
    offers = await GetStudentOffersService(project_repo).execute(message.from_user.id)
    text, total_pages = format_offer_list(offers)
    slice_, _, _ = paginate(offers, 0)
    item_kb = _build_offers_kb(slice_, 0, total_pages)
    await message.answer(text, parse_mode="Markdown", reply_markup=item_kb)


@router.callback_query(ProjectCallback.filter(F.action == ProjectAction.view_offer))
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


# ── CLOSE ACTIONS ────────────────────────────────────────────────────────
@router.callback_query(MenuCallback.filter(F.action == MenuAction.close_list))
async def cb_close_list(callback: types.CallbackQuery):
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.answer()
