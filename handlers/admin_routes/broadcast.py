import logging
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from application.admin_service import GetAllUserIdsService
from config import settings
from infrastructure.repositories import ProjectRepository
from keyboards.admin_kb import get_cancel_kb
from keyboards.callbacks import MenuCallback
from states import AdminStates
from utils.constants import MSG_BROADCAST_PROMPT, MSG_BROADCAST_SUCCESS
from utils.broadcaster import Broadcaster

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(
    MenuCallback.filter(F.action == "admin_broadcast"),
    F.from_user.id.in_(settings.admin_ids),
)
async def trigger_broadcast(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(MSG_BROADCAST_PROMPT, reply_markup=get_cancel_kb())
    await state.set_state(AdminStates.waiting_for_broadcast)


@router.message(
    AdminStates.waiting_for_broadcast, F.from_user.id.in_(settings.admin_ids)
)
async def execute_broadcast(
    message: types.Message,
    state: FSMContext,
    bot,
    project_repo: ProjectRepository,
):
    """GetAllUserIdsService fetches recipients; handler drives the broadcast loop."""
    try:
        users = await GetAllUserIdsService(project_repo).execute()
        status_msg = await message.answer("🔄 **جاري عملية الأرسال...**")
        success_count = await Broadcaster(bot).broadcast(
            users, f"🔔 **إعلان هام:**\n\n{message.text}"
        )
        await status_msg.delete()
        await message.answer(
            MSG_BROADCAST_SUCCESS.format(success_count),
            reply_markup=types.ReplyKeyboardRemove(),
        )
    except Exception as e:
        logger.error(f"Broadcast failed: {e}", exc_info=True)
        await message.answer("⚠️ حدث خطأ أثناء عملية الإرسال.")
    finally:
        await state.clear()
