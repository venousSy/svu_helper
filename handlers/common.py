"""
Common Handlers Module
======================
Manages universal bot commands like /start, /help, and /cancel, 
as well as basic main menu navigation logic.
"""

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from utils.constants import MSG_WELCOME, MSG_HELP, MSG_CANCELLED, MSG_NO_ACTIVE_PROCESS, BTN_NEW_PROJECT, BTN_MY_PROJECTS, BTN_MY_OFFERS
from keyboards.common_kb import get_student_main_kb

# --- ROUTER INITIALIZATION ---
router = Router()

@router.message(Command("start"))
async def welcome(message: types.Message):
    """Greets the user and provides basic instructions."""
    await message.answer(
        MSG_WELCOME,
        reply_markup=get_student_main_kb()
    )

@router.message(Command("help"))
async def help_command(message: types.Message):
    """Provides help information to the user."""
    await message.answer(
        MSG_HELP,
        reply_markup=get_student_main_kb()
    )

@router.message(Command("cancel"))
async def global_cancel(message: types.Message, state: FSMContext):
    """Universal cancel command to reset any active FSM state."""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer(MSG_NO_ACTIVE_PROCESS)
        return
    await state.clear()
    await message.answer(MSG_CANCELLED, reply_markup=get_student_main_kb())

# Add text handlers for the menu buttons
@router.message(lambda message: message.text in [BTN_NEW_PROJECT, BTN_MY_PROJECTS, BTN_MY_OFFERS])
async def handle_menu_buttons(message: types.Message, state: FSMContext):
    """Handle menu button clicks."""
    if message.text == BTN_NEW_PROJECT:
        await message.answer("Use /new_project command to start a new project.")
    elif message.text == BTN_MY_PROJECTS:
        await message.answer("Use /my_projects command to view your projects.")
    elif message.text == BTN_MY_OFFERS:
        await message.answer("Use /my_offers command to view your offers.")