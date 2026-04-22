import structlog
from aiogram import Router, F, types

from application.admin_service import (
    GetAllPaymentsService,
    GetCategorizedProjectsService,
    GetOngoingProjectsService,
    GetPendingProjectsService,
    GetProjectHistoryService,
)
from config import settings
from infrastructure.repositories import PaymentRepository, ProjectRepository
from keyboards.callbacks import MenuCallback, PageCallback, PageAction, MenuAction
from keyboards.factory import KeyboardFactory
from utils.formatters import (
    format_master_report,
    format_payment_list,
    format_project_history,
    format_project_list,
)
from utils.pagination import build_nav_keyboard, paginate

router = Router()
logger = structlog.get_logger(__name__)


# ── HELPER: render a single page and answer the callback ────────────────────

async def _render(
    callback: types.CallbackQuery,
    text: str,
    total_pages: int,
    action: str,
    page: int,
    back_action: str = "back_to_admin",
    extra_kb: types.InlineKeyboardMarkup | None = None,
) -> None:
    """Edit message, attach pagination footer, answer callback."""
    kb = extra_kb if extra_kb and total_pages == 1 else build_nav_keyboard(
        action=action, page=page, total_pages=total_pages, back_action=back_action
    )
    try:
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    except Exception:
        await callback.message.edit_text(text, parse_mode=None, reply_markup=kb)
    await callback.answer()


# ── MASTER REPORT (all projects, all categories) ─────────────────────────────

async def _render_master_page(
    callback: types.CallbackQuery, project_repo: ProjectRepository, page: int
) -> None:
    projects = await GetCategorizedProjectsService(project_repo).execute()
    text, total_pages = format_master_report(projects, page=page)
    await _render(callback, text, total_pages, "all_projects", page)


@router.callback_query(
    MenuCallback.filter(F.action == MenuAction.view_all_master),
    F.from_user.id.in_(settings.admin_ids),
)
async def view_all_master(
    callback: types.CallbackQuery, project_repo: ProjectRepository
):
    await _render_master_page(callback, project_repo, page=0)


@router.callback_query(
    PageCallback.filter(F.action == PageAction.all_projects),
    F.from_user.id.in_(settings.admin_ids),
)
async def view_all_page(
    callback: types.CallbackQuery,
    callback_data: PageCallback,
    project_repo: ProjectRepository,
):
    await _render_master_page(callback, project_repo, page=callback_data.page)


# ── PENDING PROJECTS ─────────────────────────────────────────────────────────

async def _render_pending(
    callback: types.CallbackQuery, project_repo: ProjectRepository, page: int
) -> None:
    projects = await GetPendingProjectsService(project_repo).execute()
    text, total_pages = format_project_list(projects, "📊 مشاريع قيد الانتظار", page=page)

    slice_, _, _ = paginate(projects, page)
    item_kb = KeyboardFactory.pending_projects(slice_)

    if total_pages > 1:
        kb = _merge_item_and_nav(item_kb, "pending", page, total_pages)
    else:
        kb = item_kb

    try:
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    except Exception:
        await callback.message.edit_text(text, parse_mode=None, reply_markup=kb)
    await callback.answer()


@router.callback_query(
    MenuCallback.filter(F.action == MenuAction.view_pending),
    F.from_user.id.in_(settings.admin_ids),
)
async def admin_view_pending(
    callback: types.CallbackQuery, project_repo: ProjectRepository
):
    await _render_pending(callback, project_repo, page=0)


@router.callback_query(
    PageCallback.filter(F.action == PageAction.pending),
    F.from_user.id.in_(settings.admin_ids),
)
async def admin_pending_page(
    callback: types.CallbackQuery,
    callback_data: PageCallback,
    project_repo: ProjectRepository,
):
    await _render_pending(callback, project_repo, page=callback_data.page)


# ── ACCEPTED / ONGOING PROJECTS ───────────────────────────────────────────────

async def _render_accepted(
    callback: types.CallbackQuery, project_repo: ProjectRepository, page: int
) -> None:
    projects = await GetOngoingProjectsService(project_repo).execute()
    text, total_pages = format_project_list(projects, "🚀 مشاريع جارية", page=page)

    slice_, _, _ = paginate(projects, page)
    item_kb = KeyboardFactory.accepted_projects(slice_)

    if total_pages > 1:
        kb = _merge_item_and_nav(item_kb, "accepted", page, total_pages)
    else:
        kb = item_kb

    try:
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    except Exception:
        await callback.message.edit_text(text, parse_mode=None, reply_markup=kb)
    await callback.answer()


@router.callback_query(
    MenuCallback.filter(F.action == MenuAction.view_accepted),
    F.from_user.id.in_(settings.admin_ids),
)
async def admin_view_accepted(
    callback: types.CallbackQuery, project_repo: ProjectRepository
):
    await _render_accepted(callback, project_repo, page=0)


@router.callback_query(
    PageCallback.filter(F.action == PageAction.accepted),
    F.from_user.id.in_(settings.admin_ids),
)
async def admin_accepted_page(
    callback: types.CallbackQuery,
    callback_data: PageCallback,
    project_repo: ProjectRepository,
):
    await _render_accepted(callback, project_repo, page=callback_data.page)


# ── HISTORY ───────────────────────────────────────────────────────────────────

async def _render_history(
    callback: types.CallbackQuery, project_repo: ProjectRepository, page: int
) -> None:
    history = await GetProjectHistoryService(project_repo).execute()
    text, total_pages = format_project_history(history, page=page)
    await _render(callback, text, total_pages, "history", page)


@router.callback_query(
    MenuCallback.filter(F.action == MenuAction.view_history),
    F.from_user.id.in_(settings.admin_ids),
)
async def admin_view_history(
    callback: types.CallbackQuery, project_repo: ProjectRepository
):
    await _render_history(callback, project_repo, page=0)


@router.callback_query(
    PageCallback.filter(F.action == PageAction.history),
    F.from_user.id.in_(settings.admin_ids),
)
async def admin_history_page(
    callback: types.CallbackQuery,
    callback_data: PageCallback,
    project_repo: ProjectRepository,
):
    await _render_history(callback, project_repo, page=callback_data.page)


# ── PAYMENTS ──────────────────────────────────────────────────────────────────

async def _render_payments(
    callback: types.CallbackQuery, payment_repo: PaymentRepository, page: int
) -> None:
    payments = await GetAllPaymentsService(payment_repo).execute()
    text, total_pages = format_payment_list(payments, page=page)
    await _render(callback, text, total_pages, "payments", page)


@router.callback_query(
    MenuCallback.filter(F.action == MenuAction.view_payments),
    F.from_user.id.in_(settings.admin_ids),
)
async def admin_view_payments(
    callback: types.CallbackQuery, payment_repo: PaymentRepository
):
    await _render_payments(callback, payment_repo, page=0)


@router.callback_query(
    PageCallback.filter(F.action == PageAction.payments),
    F.from_user.id.in_(settings.admin_ids),
)
async def admin_payments_page(
    callback: types.CallbackQuery,
    callback_data: PageCallback,
    payment_repo: PaymentRepository,
):
    await _render_payments(callback, payment_repo, page=callback_data.page)


# ── INTERNAL HELPER ───────────────────────────────────────────────────────────

def _merge_item_and_nav(
    item_kb: types.InlineKeyboardMarkup,
    action: str,
    page: int,
    total_pages: int,
) -> types.InlineKeyboardMarkup:
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram import types as tg_types
    from keyboards.callbacks import MenuCallback
    from utils.pagination import build_nav_keyboard

    builder = InlineKeyboardBuilder()
    
    # Re-add existing rows except the back button
    back_action_data = MenuCallback(action="back_to_admin").pack()
    for row in item_kb.inline_keyboard:
        if len(row) == 1 and row[0].callback_data == back_action_data:
            continue
        builder.row(*row)

    return build_nav_keyboard(
        action=action,
        page=page,
        total_pages=total_pages,
        builder=builder,
        back_callback_data=back_action_data,
    )
