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
    count = 0
    for u_id in users:
        try:
            await bot.send_message(u_id, f"🔔 **إعلان هام:**\n\n{message.text}")
            count += 1
            await asyncio.sleep(0.05)  # Prevent Telegram flood limit (30 msg/sec)
        except Exception as e:
            logger.warning(f"Failed to broadcast to {u_id}: {e}")
            continue  # Skip users who blocked the bot
    await message.answer(
        MSG_BROADCAST_SUCCESS.format(count), reply_markup=types.ReplyKeyboardRemove()
    )
    await state.clear()
