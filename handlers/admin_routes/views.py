from aiogram import Router, F, types
import logging

logger = logging.getLogger(__name__)

from config import settings
from database.repositories import ProjectRepository, PaymentRepository
from keyboards.admin_kb import (
    get_accepted_projects_kb,
    get_back_btn,
    get_payment_history_kb,
    get_pending_projects_kb,
)
from keyboards.callbacks import MenuCallback
from utils.enums import ProjectStatus
from utils.formatters import (
    format_master_report,
    format_payment_list,
    format_project_history,
    format_project_list,
)

router = Router()

@router.callback_query(MenuCallback.filter(F.action == "view_all_master"), F.from_user.id.in_(settings.admin_ids))
async def view_all_master(callback: types.CallbackQuery):
    """Fetches and displays a categorized report of every project in the database."""
    projects = await ProjectRepository.get_all_categorized()
    await callback.message.edit_text(
        format_master_report(projects),
        parse_mode="Markdown",
        reply_markup=get_back_btn().as_markup(),
    )


@router.callback_query(MenuCallback.filter(F.action == "view_pending"), F.from_user.id.in_(settings.admin_ids))
async def admin_view_pending(callback: types.CallbackQuery):
    """Lists all projects awaiting admin review with management deep-links."""
    pending = await ProjectRepository.get_projects_by_status([ProjectStatus.PENDING])
    text = format_project_list(pending, "📊 مشاريع قيد الانتظار")

    markup = get_pending_projects_kb(pending)

    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=markup)


@router.callback_query(MenuCallback.filter(F.action == "view_accepted"), F.from_user.id.in_(settings.admin_ids))
async def admin_view_accepted(callback: types.CallbackQuery):
    """Lists active/ongoing projects that are ready for final submission."""
    accepted = await ProjectRepository.get_projects_by_status([ProjectStatus.ACCEPTED, ProjectStatus.AWAITING_VERIFICATION])
    text = format_project_list(accepted, "🚀 مشاريع جارية")

    markup = get_accepted_projects_kb(accepted)

    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=markup)


@router.callback_query(MenuCallback.filter(F.action == "view_history"), F.from_user.id.in_(settings.admin_ids))
async def admin_view_history(callback: types.CallbackQuery):
    """Displays a read-only log of finished or denied projects."""
    history = await ProjectRepository.get_projects_by_status([ProjectStatus.FINISHED, ProjectStatus.DENIED_ADMIN, ProjectStatus.DENIED_STUDENT, ProjectStatus.REJECTED_PAYMENT])
    await callback.message.edit_text(
        format_project_history(history),
        parse_mode="Markdown",
        reply_markup=get_back_btn().as_markup(),
    )


@router.callback_query(MenuCallback.filter(F.action == "view_payments"), F.from_user.id.in_(settings.admin_ids))
async def admin_view_payments(callback: types.CallbackQuery):
    """Displays a log of all payments (Pending, Accepted, Rejected)."""
    payments = await PaymentRepository.get_all()
    await callback.message.edit_text(
        format_payment_list(payments),
        parse_mode="Markdown",
        reply_markup=get_payment_history_kb(payments),
    )
