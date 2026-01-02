from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

# Create the router instance that main.py is looking for
router = Router()

@router.message(Command("start"))
async def welcome(message: types.Message):
    """Greets the user and provides basic instructions."""
    await message.answer("👋 Hello! Use /new_project to submit a homework request or /my_projects to check status.")

@router.message(Command("cancel"))
async def global_cancel(message: types.Message, state: FSMContext):
    """Universal cancel command to reset any active FSM state."""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("❌ No active process to cancel.")
        return
    await state.clear()
    await message.answer("🚫 Process cancelled.", reply_markup=types.ReplyKeyboardRemove())