import asyncio
import logging
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from config import ADMIN_IDS
from database import get_all_users
from keyboards.admin_kb import get_cancel_kb
from keyboards.callbacks import MenuCallback
from states import AdminStates
from utils.constants import MSG_BROADCAST_PROMPT, MSG_BROADCAST_SUCCESS
from utils.broadcaster import Broadcaster

router = Router()
logger = logging.getLogger(__name__)

@router.callback_query(MenuCallback.filter(F.action == "admin_broadcast"), F.from_user.id.in_(ADMIN_IDS))
async def trigger_broadcast(callback: types.CallbackQuery, state: FSMContext):
    """Initiates the broadcast FSM flow."""
    await callback.message.answer(MSG_BROADCAST_PROMPT, reply_markup=get_cancel_kb())
    await state.set_state(AdminStates.waiting_for_broadcast)


@router.message(AdminStates.waiting_for_broadcast, F.from_user.id.in_(ADMIN_IDS))
async def execute_broadcast(message: types.Message, state: FSMContext, bot):
    """Sends a mass message to all unique users found in the database."""
    users = await get_all_users()
    
    # Notify admin process started for large lists
    status_msg = await message.answer("🔄 **جاري عملية الأرسال...**")
    
    broadcaster = Broadcaster(bot)
    full_text = f"🔔 **إعلان هام:**\n\n{message.text}"
    
    # Run the broadcast concurrently
    # This might take some time depending on user count
    success_count = await broadcaster.broadcast(users, full_text)
    
    await status_msg.delete()
    await message.answer(
        MSG_BROADCAST_SUCCESS.format(success_count), reply_markup=types.ReplyKeyboardRemove()
    )
    await state.clear()
