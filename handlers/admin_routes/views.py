import logging
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
from keyboards.admin_kb import (
    get_accepted_projects_kb,
    get_back_btn,
    get_payment_history_kb,
    get_pending_projects_kb,
)
from keyboards.callbacks import MenuCallback, PageCallback
from keyboards.factory import KeyboardFactory
from utils.formatters import (
    format_master_report,
    format_payment_list,
    format_project_history,
    format_project_list,
)

router = Router()
logger = logging.getLogger(__name__)

# How many projects to show per page in the master report
_PAGE_SIZE = 5


async def _render_master_page(
    callback: types.CallbackQuery,
    project_repo: ProjectRepository,
    page: int,
) -> None:
    """Fetch categorized projects and edit the message to show the requested page."""
    projects = await GetCategorizedProjectsService(project_repo).execute()
    text, total_pages = format_master_report(projects, page=page, page_size=_PAGE_SIZE)
    kb = KeyboardFactory.paginated_master_report(page=page, total_pages=total_pages)
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    await callback.answer()


@router.callback_query(
    MenuCallback.filter(F.action == "view_all_master"),
    F.from_user.id.in_(settings.admin_ids),
)
async def view_all_master(
    callback: types.CallbackQuery, project_repo: ProjectRepository
):
    await _render_master_page(callback, project_repo, page=0)


@router.callback_query(
    PageCallback.filter(F.action == "all_projects"),
    F.from_user.id.in_(settings.admin_ids),
)
async def view_all_page(
    callback: types.CallbackQuery,
    callback_data: PageCallback,
    project_repo: ProjectRepository,
):
    await _render_master_page(callback, project_repo, page=callback_data.page)


@router.callback_query(
    MenuCallback.filter(F.action == "view_pending"),
    F.from_user.id.in_(settings.admin_ids),
)
async def admin_view_pending(
    callback: types.CallbackQuery, project_repo: ProjectRepository
):
    pending = await GetPendingProjectsService(project_repo).execute()
    await callback.message.edit_text(
        format_project_list(pending, "📊 مشاريع قيد الانتظار"),
        parse_mode="Markdown",
        reply_markup=get_pending_projects_kb(pending),
    )


@router.callback_query(
    MenuCallback.filter(F.action == "view_accepted"),
    F.from_user.id.in_(settings.admin_ids),
)
async def admin_view_accepted(
    callback: types.CallbackQuery, project_repo: ProjectRepository
):
    ongoing = await GetOngoingProjectsService(project_repo).execute()
    await callback.message.edit_text(
        format_project_list(ongoing, "🚀 مشاريع جارية"),
        parse_mode="Markdown",
        reply_markup=get_accepted_projects_kb(ongoing),
    )


@router.callback_query(
    MenuCallback.filter(F.action == "view_history"),
    F.from_user.id.in_(settings.admin_ids),
)
async def admin_view_history(
    callback: types.CallbackQuery, project_repo: ProjectRepository
):
    history = await GetProjectHistoryService(project_repo).execute()
    await callback.message.edit_text(
        format_project_history(history),
        parse_mode="Markdown",
        reply_markup=get_back_btn().as_markup(),
    )


@router.callback_query(
    MenuCallback.filter(F.action == "view_payments"),
    F.from_user.id.in_(settings.admin_ids),
)
async def admin_view_payments(
    callback: types.CallbackQuery, payment_repo: PaymentRepository
):
    payments = await GetAllPaymentsService(payment_repo).execute()
    await callback.message.edit_text(
        format_payment_list(payments),
        parse_mode="Markdown",
        reply_markup=get_payment_history_kb(payments),
    )
