from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from config import settings
from database.repositories import StatsRepository, SettingsRepository
from keyboards.admin_kb import get_admin_dashboard_kb
from keyboards.callbacks import MenuCallback
from utils.constants import BTN_CANCEL, MSG_ADMIN_DASHBOARD, MSG_CANCELLED

router = Router()

@router.message(F.text == BTN_CANCEL, F.from_user.id.in_(settings.ADMIN_IDS))
async def admin_cancel_process(message: types.Message, state: FSMContext):
    """Cancels any active admin FSM state."""
    current_state = await state.get_state()
    if current_state:
        await state.clear()
        await message.answer(MSG_CANCELLED, reply_markup=types.ReplyKeyboardRemove())
        await admin_dashboard(message)  # Return to dashboard
    else:
        await admin_dashboard(message)


@router.message(Command("admin"), F.from_user.id.in_(settings.ADMIN_IDS))
async def admin_dashboard(message: types.Message):
    """Entry point: Displays the administrative control panel."""
    await message.answer(MSG_ADMIN_DASHBOARD, reply_markup=get_admin_dashboard_kb())


@router.callback_query(MenuCallback.filter(F.action == "back_to_admin"), F.from_user.id.in_(settings.ADMIN_IDS))
async def back_to_admin(callback: types.CallbackQuery):
    """Returns the user to the main dashboard menu."""
    await callback.message.edit_text(
        MSG_ADMIN_DASHBOARD,
        parse_mode="Markdown",
        reply_markup=get_admin_dashboard_kb(),
    )


@router.message(Command("stats"), F.from_user.id.in_(settings.ADMIN_IDS))
async def admin_stats_handler(message: types.Message):
    """Displays project statistics."""
    stats = await StatsRepository.get_stats()
    text = (
        "📊 **إحصائيات البوت**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"📦 **شامل:** {stats['total']}\n"
        f"⏳ **قيد الانتظار:** {stats['pending']}\n"
        f"🚀 **نشط / جاري:** {stats['active']}\n"
        f"✅ **منتهي:** {stats['finished']}\n"
        f"⛔ **مرفوض:** {stats['denied']}\n"
    )
    await message.answer(text, parse_mode="Markdown")


@router.message(Command("maintenance_on"), F.from_user.id.in_(settings.ADMIN_IDS))
async def admin_maintenance_on(message: types.Message):
    """Enables maintenance mode."""
    await SettingsRepository.set_maintenance_mode(True)
    await message.answer("🛑 **تم تفعيل وضع الصيانة.**\nلن يتمكن المستخدمون من استخدام البوت.")


@router.message(Command("maintenance_off"), F.from_user.id.in_(settings.ADMIN_IDS))
async def admin_maintenance_off(message: types.Message):
    """Disables maintenance mode."""
    await SettingsRepository.set_maintenance_mode(False)
    await message.answer("✅ **تم إيقاف وضع الصيانة.**\nالبوت متاح للجميع الآن.")
