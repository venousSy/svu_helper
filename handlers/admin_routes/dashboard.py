import math

from aiogram import Router, F, types, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import structlog

from application.admin_service import GetStatsService, MaintenanceService
from config import settings
from infrastructure.repositories import SettingsRepository, StatsRepository, TicketRepository
from keyboards.callbacks import MenuCallback, MenuAction, PageCallback, PageAction
from keyboards.factory import KeyboardFactory
from utils.constants import BTN_CANCEL, MSG_ADMIN_DASHBOARD, MSG_CANCELLED
from utils.formatters import format_datetime
from utils.helpers import build_ticket_service
from utils.pagination import build_nav_keyboard

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
    await message.answer(MSG_ADMIN_DASHBOARD, reply_markup=KeyboardFactory.admin_dashboard())


@router.callback_query(
    MenuCallback.filter(F.action == MenuAction.back_to_admin),
    F.from_user.id.in_(settings.admin_ids),
)
async def back_to_admin(callback: types.CallbackQuery):
    await callback.message.edit_text(
        MSG_ADMIN_DASHBOARD, parse_mode="Markdown", reply_markup=KeyboardFactory.admin_dashboard()
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





async def _render_admin_tickets(
    callback: types.CallbackQuery, service, page: int
):
    page_size = 5
    tickets, total_count = await service.get_all_active_tickets(
        page=page, page_size=page_size
    )

    if total_count == 0:
        await callback.message.edit_text(
            "📭 لا توجد تذاكر مفتوحة حالياً.",
            reply_markup=KeyboardFactory.back(),
        )
        return

    lines = ["🎫 **التذاكر المفتوحة** 🎫\n"]
    for t in tickets:
        tid = t["ticket_id"]
        # Determine user name
        username = t.get("username")
        full_name = t.get("user_full_name")
        display_name = f"@{username}" if username else (full_name or f"مستخدم {t['user_id']}")

        # Format date
        created = format_datetime(t.get("created_at", ""), fmt="%Y-%m-%d %H:%M")
            
        # Get last message
        messages = t.get("messages", [])
        last_msg = ""
        if messages:
            last_msg_obj = messages[-1]
            last_msg_text = last_msg_obj.get("text") or "مرفق 📎"
            # Trim message if too long
            if len(last_msg_text) > 40:
                last_msg_text = last_msg_text[:37] + "..."
            last_msg = f"💬 آخر رسالة: {last_msg_text}"

        lines.append(f"🔹 **تذكرة #{tid}**")
        lines.append(f"👤 {display_name}")
        lines.append(f"📅 {created}")
        lines.append(f"{last_msg}\n")

    total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1

    text = "\n".join(lines)
    kb = build_nav_keyboard(action=PageAction.admin_tickets_page, page=page, total_pages=total_pages)
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)


@router.callback_query(
    MenuCallback.filter(F.action == MenuAction.admin_tickets),
    F.from_user.id.in_(settings.admin_ids),
)
async def view_admin_tickets(
    callback: types.CallbackQuery, ticket_repo: TicketRepository, bot: Bot
):
    service = build_ticket_service(ticket_repo, bot)
    await _render_admin_tickets(callback, service, 0)


@router.callback_query(
    PageCallback.filter(F.action == PageAction.admin_tickets_page),
    F.from_user.id.in_(settings.admin_ids),
)
async def view_admin_tickets_page(
    callback: types.CallbackQuery,
    callback_data: PageCallback,
    ticket_repo: TicketRepository,
    bot: Bot,
):
    service = build_ticket_service(ticket_repo, bot)
    await _render_admin_tickets(callback, service, callback_data.page)
