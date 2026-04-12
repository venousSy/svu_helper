"""
Common Handlers Module
======================
Manages universal bot commands like /start, /help, and /cancel,
as well as basic main menu navigation logic.
"""

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from utils.constants import (
    BTN_MY_OFFERS,
    BTN_MY_PROJECTS,
    BTN_NEW_PROJECT,
    MSG_CANCELLED,
    MSG_HELP,
    MSG_NO_ACTIVE_PROCESS,
    MSG_WELCOME,
)
from keyboards.common_kb import get_student_main_kb
from keyboards.callbacks import MenuCallback, MenuAction
from keyboards.calendar_kb import build_calendar, CalendarCallback
from states import ProjectOrder, AdminStates
from utils.constants import MSG_ASK_DETAILS, MSG_ASK_NOTES
from keyboards.admin_kb import get_notes_decision_kb

# --- ROUTER INITIALIZATION ---
router = Router()


@router.message(Command("start"))
async def welcome(message: types.Message):
    """Greets the user and provides basic instructions."""
    await message.answer(MSG_WELCOME, reply_markup=get_student_main_kb())


@router.message(Command("help"))
async def help_command(message: types.Message):
    """Provides help information to the user."""
    await message.answer(MSG_HELP, reply_markup=types.ReplyKeyboardRemove())

@router.callback_query(MenuCallback.filter(F.action == MenuAction.help))
async def cb_help(callback: types.CallbackQuery):
    await callback.message.answer(MSG_HELP)
    await callback.answer()


@router.message(Command("cancel"))
async def global_cancel(message: types.Message, state: FSMContext):
    """Universal cancel command to reset any active FSM state."""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer(
            MSG_NO_ACTIVE_PROCESS, reply_markup=types.ReplyKeyboardRemove()
        )
        return
    await state.clear()
    await message.answer(MSG_CANCELLED, reply_markup=types.ReplyKeyboardRemove())

@router.callback_query(CalendarCallback.filter())
async def process_calendar(callback: types.CallbackQuery, callback_data: CalendarCallback, state: FSMContext):
    action = callback_data.action
    year = callback_data.year
    month = callback_data.month
    day = callback_data.day

    if action == "ignore":
        return await callback.answer()

    if action == "nav":
        await callback.message.edit_reply_markup(reply_markup=build_calendar(year, month))
        return await callback.answer()

    if action == "day":
        date_str = f"{year:04d}-{month:02d}-{day:02d}"
        current_state = await state.get_state()
        
        # Remove the calendar
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass

        if current_state == ProjectOrder.deadline.state:
            await state.update_data(deadline=date_str)
            await callback.message.answer(MSG_ASK_DETAILS, parse_mode="Markdown")
            await state.set_state(ProjectOrder.details)
            
        elif current_state == AdminStates.waiting_for_delivery.state:
            await state.update_data(delivery=date_str)
            await callback.message.answer(MSG_ASK_NOTES, reply_markup=get_notes_decision_kb())
            await state.set_state(AdminStates.waiting_for_notes_decision)

    # Always answer the callback to dismiss the spinner, regardless of state
    await callback.answer()
