import math

from aiogram import Router, F, types, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import structlog

from application.admin_service import GetStatsService, MaintenanceService
from config import settings
from infrastructure.repositories import SettingsRepository, StatsRepository, TicketRepository, ProjectRepository
from keyboards.callbacks import MenuCallback, MenuAction, PageCallback, PageAction
from keyboards.factory import KeyboardFactory
from utils.constants import (
    BTN_CANCEL,
    MSG_ADMIN_ATTACHMENT_LABEL,
    MSG_ADMIN_DASHBOARD,
    MSG_ADMIN_LAST_MESSAGE,
    MSG_ADMIN_NO_OPEN_TICKETS,
    MSG_ADMIN_TICKET_LINE,
    MSG_ADMIN_TICKETS_HEADER,
    MSG_ADMIN_USER_FALLBACK,
    MSG_CANCELLED,
    MSG_MAINTENANCE_OFF,
    MSG_MAINTENANCE_ON,
    MSG_STATS_REPORT,
    MSG_TESTS_RUNNING,
    MSG_TESTS_SUCCESS,
    MSG_TESTS_FAILED,
    MSG_TESTS_ERROR,
)
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

import asyncio
import html

@router.callback_query(
    MenuCallback.filter(F.action == MenuAction.admin_test_menu),
    F.from_user.id.in_(settings.admin_ids),
)
async def admin_test_menu_handler(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "اختر نوع الاختبارات التي تريد تشغيلها:", 
        reply_markup=KeyboardFactory.test_actions()
    )


@router.callback_query(
    MenuCallback.filter(F.action.in_([MenuAction.admin_run_all_tests, MenuAction.admin_run_failed_tests])),
    F.from_user.id.in_(settings.admin_ids),
)
async def execute_tests_handler(callback: types.CallbackQuery, callback_data: MenuCallback):
    await callback.answer()
    loading_msg = await callback.message.edit_text(MSG_TESTS_RUNNING, parse_mode="HTML")
    
    command = "python tests/e2e_runner.py"
    if callback_data.action == MenuAction.admin_run_failed_tests:
        command += " --failed-only"
        
    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        output = stdout.decode('utf-8')
        err_output = stderr.decode('utf-8')
        
        full_output = (output + "\n" + err_output).strip()
        full_output = html.escape(full_output)
        
        if len(full_output) > 3000:
            full_output = full_output[-3000:]
            
        await loading_msg.delete()
        if process.returncode == 0:
            await callback.message.answer(
                MSG_TESTS_SUCCESS.format(full_output),
                parse_mode="HTML"
            )
        else:
            await callback.message.answer(
                MSG_TESTS_FAILED.format(full_output),
                parse_mode="HTML"
            )
    except Exception as e:
        logger.error("Error running E2E tests", error=str(e))
        try:
            await loading_msg.delete()
        except:
            pass
        await callback.message.answer(
            MSG_TESTS_ERROR.format(str(e)),
            parse_mode="HTML"
        )

@router.message(Command("stats"), F.from_user.id.in_(settings.admin_ids))
async def admin_stats_handler(message: types.Message, stats_repo: StatsRepository):
    stats = await GetStatsService(stats_repo).execute()
    text = MSG_STATS_REPORT.format(
        stats['total'],
        stats['pending'],
        stats['active'],
        stats['finished'],
        stats['denied'],
    )
    await message.answer(text, parse_mode="Markdown")


@router.message(Command("maintenance_on"), F.from_user.id.in_(settings.admin_ids))
async def admin_maintenance_on(message: types.Message, settings_repo: SettingsRepository):
    await MaintenanceService(settings_repo).enable()
    logger.warning("Maintenance mode ENABLED", admin_id=message.from_user.id)
    await message.answer(MSG_MAINTENANCE_ON)


@router.message(Command("maintenance_off"), F.from_user.id.in_(settings.admin_ids))
async def admin_maintenance_off(message: types.Message, settings_repo: SettingsRepository):
    await MaintenanceService(settings_repo).disable()
    logger.warning("Maintenance mode DISABLED", admin_id=message.from_user.id)
    await message.answer(MSG_MAINTENANCE_OFF)





async def _render_admin_tickets(
    callback: types.CallbackQuery, service, page: int
):
    page_size = 5
    tickets, total_count = await service.get_all_active_tickets(
        page=page, page_size=page_size
    )

    if total_count == 0:
        await callback.message.edit_text(
            MSG_ADMIN_NO_OPEN_TICKETS,
            reply_markup=KeyboardFactory.back(),
        )
        return

    lines = [MSG_ADMIN_TICKETS_HEADER + "\n"]
    for t in tickets:
        tid = t["ticket_id"]
        # Determine user name
        username = t.get("username")
        full_name = t.get("user_full_name")
        display_name = f"@{username}" if username else (full_name or MSG_ADMIN_USER_FALLBACK.format(t['user_id']))

        # Format date
        created = format_datetime(t.get("created_at", ""), fmt="%Y-%m-%d %H:%M")
            
        # Get last message
        messages = t.get("messages", [])
        last_msg = ""
        if messages:
            last_msg_obj = messages[-1]
            last_msg_text = last_msg_obj.get("text") or MSG_ADMIN_ATTACHMENT_LABEL
            # Trim message if too long
            if len(last_msg_text) > 40:
                last_msg_text = last_msg_text[:37] + "..."
            last_msg = MSG_ADMIN_LAST_MESSAGE.format(last_msg_text)

        lines.append(MSG_ADMIN_TICKET_LINE.format(tid))
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


@router.callback_query(
    MenuCallback.filter(F.action == MenuAction.admin_urgent_cases),
    F.from_user.id.in_(settings.admin_ids),
)
async def view_admin_urgent_cases(
    callback: types.CallbackQuery, project_repo: ProjectRepository
):
    from utils.constants import MSG_NO_URGENT_CASES, MSG_URGENT_REPORT_HEADER, MSG_URGENT_REPORT_ITEM
    
    urgent_projects = await project_repo.get_urgent_projects()
    
    if not urgent_projects:
        await callback.message.edit_text(
            MSG_NO_URGENT_CASES,
            reply_markup=KeyboardFactory.back()
        )
        return
        
    text = MSG_URGENT_REPORT_HEADER
    for p in urgent_projects:
        subject = p.get('subject_name', 'N/A')
        status = p.get('status', 'N/A')
        text += MSG_URGENT_REPORT_ITEM.format(p['id'], subject, status)
        
    await callback.message.edit_text(
        text, reply_markup=KeyboardFactory.back()
    )


