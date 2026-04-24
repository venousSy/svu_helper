import structlog
from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramAPIError

from application.project_service import AddProjectService
from config import settings
from infrastructure.repositories import ProjectRepository
from keyboards.callbacks import MenuCallback, MenuAction
from keyboards.calendar_kb import build_calendar, CalendarCallback
from keyboards.factory import KeyboardFactory
from states import ProjectOrder
from utils.constants import (
    MSG_ASK_DEADLINE,
    MSG_ASK_DETAILS,
    MSG_ASK_SUBJECT,
    MSG_ASK_TUTOR,
    MSG_FILE_TOO_LARGE,
    MSG_MEDIA_BEFORE_TEXT,
    MSG_NO_DESC,
    MSG_PROJECT_SUBMIT_ERROR,
    MSG_SUBJECT_TOO_LONG,
    MSG_TUTOR_TOO_LONG,
    MSG_DEADLINE_TOO_LONG,
    BTN_NEW_PROJECT,
    MSG_PROJECT_SUBMITTED,
    BTN_DONE,
    MSG_DETAILS_RECEIVED,
    MSG_SEND_NEXT,
)
from utils.formatters import format_admin_notification
from utils.helpers import get_file_id, get_file_size, notify_admins

router = Router()
logger = structlog.get_logger(__name__)

MAX_FILE_SIZE_MB = AddProjectService.MAX_FILE_SIZE_MB
MAX_FILE_SIZE_BYTES = AddProjectService.MAX_FILE_SIZE_BYTES

# ── PROJECT SUBMISSION FSM ──────────────────────────────────────────────────

@router.callback_query(MenuCallback.filter(F.action == MenuAction.new_project))
async def cb_start_project(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        MSG_ASK_SUBJECT, 
        parse_mode="Markdown",
        reply_markup=KeyboardFactory.inline_cancel()
    )
    await state.set_state(ProjectOrder.subject)
    await callback.answer()


@router.message(F.text == BTN_NEW_PROJECT)
@router.message(Command("new_project"))
async def start_project(message: types.Message, state: FSMContext):
    await message.answer(
        MSG_ASK_SUBJECT, 
        parse_mode="Markdown",
        reply_markup=KeyboardFactory.inline_cancel()
    )
    await state.set_state(ProjectOrder.subject)


@router.message(ProjectOrder.subject, F.text, ~F.text.startswith('/'))
async def process_subject(message: types.Message, state: FSMContext):
    if len(message.text) > AddProjectService.MAX_SUBJECT_LENGTH:
        return await message.answer(
            MSG_SUBJECT_TOO_LONG.format(AddProjectService.MAX_SUBJECT_LENGTH)
        )
    await state.update_data(subject=message.text)
    await message.answer(
        MSG_ASK_TUTOR, 
        parse_mode="Markdown",
        reply_markup=KeyboardFactory.inline_cancel()
    )
    await state.set_state(ProjectOrder.tutor)


async def _ask_deadline(message: types.Message):
    """Helper to send the deadline prompt with the calendar inline keyboard."""
    cancel_data = MenuCallback(action=MenuAction.cancel_flow).pack()
    await message.answer(
        MSG_ASK_DEADLINE, 
        parse_mode="Markdown", 
        reply_markup=build_calendar(cancel_callback_data=cancel_data)
    )

@router.message(ProjectOrder.tutor, F.text, ~F.text.startswith('/'))
async def process_tutor(message: types.Message, state: FSMContext):
    if len(message.text) > AddProjectService.MAX_TUTOR_LENGTH:
        return await message.answer(
            MSG_TUTOR_TOO_LONG.format(AddProjectService.MAX_TUTOR_LENGTH)
        )
    await state.update_data(tutor=message.text)
    await _ask_deadline(message)
    await state.set_state(ProjectOrder.deadline)


from domain.entities import _parse_deadline
from config import settings
from utils.date_parser import parse_date_with_gemini
from keyboards.callbacks import DateConfirmCallback, DateConfirmAction
from utils.constants import (
    MSG_GEMINI_DATE_CONFIRM,
    MSG_GEMINI_DATE_INVALID,
    MSG_GEMINI_DATE_ACCEPTED,
    MSG_GEMINI_DATE_REJECTED,
)

@router.message(ProjectOrder.deadline, F.text, ~F.text.startswith('/'))
async def process_deadline(message: types.Message, state: FSMContext):
    if len(message.text) > AddProjectService.MAX_DEADLINE_LENGTH:
        await message.answer(MSG_DEADLINE_TOO_LONG)
        return await _ask_deadline(message)

    # --- Step 1: Try standard regex-based parsing ---
    try:
        valid_date = _parse_deadline(message.text)
    except ValueError:
        # --- Step 2: Gemini AI fallback ---
        if settings.GEMINI_API_KEY:
            gemini_date = await parse_date_with_gemini(
                message.text, settings.GEMINI_API_KEY
            )
            if gemini_date:
                # Show confirmation keyboard — do NOT save yet
                await message.answer(
                    MSG_GEMINI_DATE_CONFIRM.format(gemini_date),
                    parse_mode="Markdown",
                    reply_markup=KeyboardFactory.confirm_date(gemini_date),
                )
                return
            else:
                # Gemini couldn't parse either
                await message.answer(MSG_GEMINI_DATE_INVALID)
                return await _ask_deadline(message)
        else:
            # No API key — fall back to standard error
            await message.answer(f"⚠️ {MSG_GEMINI_DATE_INVALID}")
            return await _ask_deadline(message)

    # Standard parsing succeeded
    await state.update_data(deadline=valid_date)
    await message.answer(MSG_ASK_DETAILS, parse_mode="Markdown")
    await state.set_state(ProjectOrder.details)


@router.callback_query(
    DateConfirmCallback.filter(F.action == DateConfirmAction.accept),
    ProjectOrder.deadline,
)
async def accept_gemini_date(
    callback: types.CallbackQuery,
    callback_data: DateConfirmCallback,
    state: FSMContext,
):
    """User accepted the Gemini-parsed date."""
    confirmed_date = callback_data.date

    # Validate the confirmed date isn't in the past (safety check)
    try:
        _parse_deadline(confirmed_date)
    except ValueError as e:
        await callback.message.answer(f"⚠️ {e}")
        await callback.answer()
        return await _ask_deadline(callback.message)

    await state.update_data(deadline=confirmed_date)

    try:
        await callback.message.edit_text(
            MSG_GEMINI_DATE_ACCEPTED, parse_mode="Markdown"
        )
    except Exception:
        pass

    await callback.message.answer(MSG_ASK_DETAILS, parse_mode="Markdown")
    await state.set_state(ProjectOrder.details)
    await callback.answer()


@router.callback_query(
    DateConfirmCallback.filter(F.action == DateConfirmAction.reject),
    ProjectOrder.deadline,
)
async def reject_gemini_date(
    callback: types.CallbackQuery,
    callback_data: DateConfirmCallback,
    state: FSMContext,
):
    """User rejected the Gemini-parsed date — re-prompt."""
    try:
        await callback.message.edit_text(
            MSG_GEMINI_DATE_REJECTED, parse_mode="Markdown"
        )
    except Exception:
        pass

    await _ask_deadline(callback.message)
    await callback.answer()


@router.message(ProjectOrder.subject)
@router.message(ProjectOrder.tutor)
@router.message(ProjectOrder.deadline)
async def reject_media_early(message: types.Message):
    await message.answer(MSG_MEDIA_BEFORE_TEXT)


def _build_details_kb():
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_DONE)]
        ],
        resize_keyboard=True
    )

@router.message(ProjectOrder.details, F.text == BTN_DONE)
async def finalize_project(
    message: types.Message,
    state: FSMContext,
    bot,
    project_repo: ProjectRepository,
):
    data = await state.get_data()
    attachments = data.get("attachments", [])
    details_text = data.get("details_text", "").strip()

    if not attachments and not details_text:
        details_text = MSG_NO_DESC

    user = message.from_user
    try:
        project_id = await AddProjectService(project_repo).execute(
            user_id=user.id,
            username=user.username,
            user_full_name=user.full_name,
            subject=data.get("subject", ""),
            tutor=data.get("tutor", ""),
            deadline=data.get("deadline", ""),
            details=details_text,
            attachments=attachments,
        )
        await message.answer(
            MSG_PROJECT_SUBMITTED.format(project_id),
            parse_mode="Markdown",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        admin_text = format_admin_notification(
            project_id, data.get("subject", ""), data.get("deadline", ""), details_text,
            user_name=user.full_name, username=user.username,
        )
        await notify_admins(
            bot, admin_text,
            reply_markup=KeyboardFactory.new_project_alert(project_id),
        )
        await state.clear()

    except ValueError as e:
        await message.answer(f"⚠️ {e}", reply_markup=types.ReplyKeyboardRemove())
        await state.clear()
    except Exception as e:
        logger.error("Failed to submit project", error=str(e), exc_info=True)
        await message.answer(
            MSG_PROJECT_SUBMIT_ERROR,
            reply_markup=types.ReplyKeyboardRemove(),
        )
        await state.clear()

@router.message(ProjectOrder.details)
async def process_details_accumulation(
    message: types.Message,
    state: FSMContext,
):
    file_size = get_file_size(message)
    if file_size and file_size > MAX_FILE_SIZE_BYTES:
        await message.answer(MSG_FILE_TOO_LARGE.format(MAX_FILE_SIZE_MB))
        return

    data = await state.get_data()
    attachments = data.get("attachments", [])
    details_text = data.get("details_text", "")

    file_id, file_type = get_file_id(message)
    if file_id and file_type:
        attachments.append({"file_id": file_id, "file_type": file_type})

    # Append text or caption
    text_content = message.text or message.caption
    if text_content and text_content != BTN_DONE:
        if details_text:
            details_text += "\n" + text_content
        else:
            details_text = text_content

    await state.update_data(attachments=attachments, details_text=details_text)
    
    # Calculate total received items (files + non-empty text blocks)
    total_received = len(attachments) + (1 if details_text else 0)
    
    await message.answer(
        MSG_DETAILS_RECEIVED.format(total_received),
        reply_markup=_build_details_kb()
    )
