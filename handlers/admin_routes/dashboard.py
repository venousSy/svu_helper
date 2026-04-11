import logging
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import structlog

from application.admin_service import GetStatsService, MaintenanceService
from config import settings
from infrastructure.repositories import SettingsRepository, StatsRepository
from keyboards.admin_kb import get_admin_dashboard_kb
from keyboards.callbacks import MenuCallback, MenuAction
from utils.constants import BTN_CANCEL, MSG_ADMIN_DASHBOARD, MSG_CANCELLED

router = Router()
logger = structlog.get_logger()


@router.message(F.text == BTN_CANCEL, F.from_user.id.in_(settings.admin_ids))
async def admin_cancel_process(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state:
        await state.clear()
        await message.answer(MSG_CANCELLED, reply_markup=types.ReplyKeyboardRemove())
    await admin_dashboard(message)


@router.message(Command("admin"), F.from_user.id.in_(settings.admin_ids))
async def admin_dashboard(message: types.Message):
    await message.answer(MSG_ADMIN_DASHBOARD, reply_markup=get_admin_dashboard_kb())


@router.callback_query(
    MenuCallback.filter(F.action == MenuAction.back_to_admin),
    F.from_user.id.in_(settings.admin_ids),
)
async def back_to_admin(callback: types.CallbackQuery):
    await callback.message.edit_text(
        MSG_ADMIN_DASHBOARD, parse_mode="Markdown", reply_markup=get_admin_dashboard_kb()
    )


@router.message(Command("stats"), F.from_user.id.in_(settings.admin_ids))
async def admin_stats_handler(message: types.Message, stats_repo: StatsRepository):
    stats = await GetStatsService(stats_repo).execute()
    text = (
        "📊 **إحصائيات البوت**\n━━━━━━━━━━━━━━━━━━\n"
        f"📦 **شامل:** {stats['total']}\n"
        f"⏳ **قيد الانتظار:** {stats['pending']}\n"
        f"🚀 **نشط / جاري:** {stats['active']}\n"
        f"✅ **منتهي:** {stats['finished']}\n"
        f"⛔ **مرفوض:** {stats['denied']}\n"
    )
    await message.answer(text, parse_mode="Markdown")


@router.message(Command("maintenance_on"), F.from_user.id.in_(settings.admin_ids))
async def admin_maintenance_on(message: types.Message, settings_repo: SettingsRepository):
    await MaintenanceService(settings_repo).enable()
    logger.warning("Maintenance mode ENABLED", admin_id=message.from_user.id)
    await message.answer("🛑 **تم تفعيل وضع الصيانة.**\nلن يتمكن المستخدمون من استخدام البوت.")


@router.message(Command("maintenance_off"), F.from_user.id.in_(settings.admin_ids))
async def admin_maintenance_off(message: types.Message, settings_repo: SettingsRepository):
    await MaintenanceService(settings_repo).disable()
    logger.warning("Maintenance mode DISABLED", admin_id=message.from_user.id)
    await message.answer("✅ **تم إيقاف وضع الصيانة.**\nالبوت متاح للجميع الآن.")
