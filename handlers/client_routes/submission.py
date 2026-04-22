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
            MSG_SUBJECT_TOO_LONG.format(AddProjectService.MAX_SUBJECT_LENGTH)
        )
    await state.update_data(subject=message.text)
    await message.answer(MSG_ASK_TUTOR, parse_mode="Markdown")
    await state.set_state(ProjectOrder.tutor)


async def _ask_deadline(message: types.Message):
    """Helper to send the deadline prompt with the calendar inline keyboard."""
    await message.answer(MSG_ASK_DEADLINE, parse_mode="Markdown", reply_markup=build_calendar())

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

@router.message(ProjectOrder.deadline, F.text, ~F.text.startswith('/'))
async def process_deadline(message: types.Message, state: FSMContext):
    if len(message.text) > AddProjectService.MAX_DEADLINE_LENGTH:
        await message.answer(MSG_DEADLINE_TOO_LONG)
        return await _ask_deadline(message)
        
    try:
        valid_date = _parse_deadline(message.text)
    except ValueError as e:
        # e contains the user-friendly Arabic error message from _parse_deadline
        await message.answer(f"⚠️ {e}")
        return await _ask_deadline(message)
        
    await state.update_data(deadline=valid_date)
    await message.answer(MSG_ASK_DETAILS, parse_mode="Markdown")
    await state.set_state(ProjectOrder.details)


@router.message(ProjectOrder.subject)
@router.message(ProjectOrder.tutor)
@router.message(ProjectOrder.deadline)
async def reject_media_early(message: types.Message):
    await message.answer(MSG_MEDIA_BEFORE_TEXT)


@router.message(ProjectOrder.details)
async def process_details(
    message: types.Message,
    state: FSMContext,
    bot,
    project_repo: ProjectRepository,
):
    file_size = get_file_size(message)
    if file_size and file_size > MAX_FILE_SIZE_BYTES:
        await message.answer(MSG_FILE_TOO_LARGE.format(MAX_FILE_SIZE_MB))
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
