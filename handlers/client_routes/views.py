import logging
from aiogram import F, Router, types
from aiogram.filters import Command

from application.project_service import GetOfferDetailService, GetStudentOffersService, GetStudentProjectsService
from infrastructure.repositories import ProjectRepository
from keyboards.client_kb import get_offer_actions_kb, get_offers_list_kb
from keyboards.callbacks import MenuCallback, PageCallback, ProjectCallback, ProjectAction, PageAction, MenuAction
from utils.constants import (
    BTN_MY_PROJECTS,
    BTN_MY_OFFERS,
    MSG_OFFER_DETAILS,
)
from utils.formatters import (
    escape_md,
    format_offer_list,
    format_student_projects,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from utils.pagination import build_nav_keyboard, paginate
from middlewares.throttling import ThrottlingMiddleware

router = Router()
logger = logging.getLogger(__name__)

router.message.middleware(ThrottlingMiddleware(rate_limit=0.5))


@router.callback_query(MenuCallback.filter(F.action == MenuAction.my_projects))
async def cb_view_projects(
    callback: types.CallbackQuery, project_repo: ProjectRepository
):
    await _render_my_projects(callback, project_repo, page=0)


async def _render_my_projects(
    callback: types.CallbackQuery, project_repo: ProjectRepository, page: int
) -> None:
    projects = await GetStudentProjectsService(project_repo).execute(callback.from_user.id)
    text, total_pages = format_student_projects(projects, page=page)
    kb = build_nav_keyboard(
        action="my_projects", page=page, total_pages=total_pages, back_action=MenuAction.close_list
    )
    
    try:
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    except Exception:
        pass
    await callback.answer()


@router.callback_query(PageCallback.filter(F.action == PageAction.my_projects))
async def cb_my_projects_page(
    callback: types.CallbackQuery,
    callback_data: PageCallback,
    project_repo: ProjectRepository,
):
    await _render_my_projects(callback, project_repo, page=callback_data.page)


@router.message(F.text == BTN_MY_PROJECTS)
@router.message(Command("my_projects"))
async def view_projects(message: types.Message, project_repo: ProjectRepository):
    projects = await GetStudentProjectsService(project_repo).execute(message.from_user.id)
    text, total_pages = format_student_projects(projects)
    kb = build_nav_keyboard(
        action="my_projects", page=0, total_pages=total_pages, back_action=MenuAction.close_list
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=kb)


@router.callback_query(MenuCallback.filter(F.action == MenuAction.my_offers))
async def cb_view_offers(
    callback: types.CallbackQuery, project_repo: ProjectRepository
):
    await _render_my_offers(callback, project_repo, page=0)


def _build_offers_kb(slice_, page: int, total_pages: int):
    builder = InlineKeyboardBuilder()
    item_kb = get_offers_list_kb(slice_)
    for row in item_kb.inline_keyboard:
        builder.row(*row)
    
    return build_nav_keyboard(
        action="my_offers",
        page=page,
        total_pages=total_pages,
        back_action=MenuAction.close_list,
        builder=builder,
    )


async def _render_my_offers(
    callback: types.CallbackQuery, project_repo: ProjectRepository, page: int
) -> None:
    offers = await GetStudentOffersService(project_repo).execute(callback.from_user.id)
    text, total_pages = format_offer_list(offers, page=page)
    slice_, _, _ = paginate(offers, page)
    item_kb = _build_offers_kb(slice_, page, total_pages)
        
    try:
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=item_kb)
    except Exception:
        pass
    await callback.answer()


@router.callback_query(PageCallback.filter(F.action == PageAction.my_offers))
async def cb_my_offers_page(
    callback: types.CallbackQuery,
    callback_data: PageCallback,
    project_repo: ProjectRepository,
):
    await _render_my_offers(callback, project_repo, page=callback_data.page)


@router.message(F.text == BTN_MY_OFFERS)
@router.message(Command("my_offers"))
async def view_offers(message: types.Message, project_repo: ProjectRepository):
    offers = await GetStudentOffersService(project_repo).execute(message.from_user.id)
    text, total_pages = format_offer_list(offers)
    slice_, _, _ = paginate(offers, 0)
    item_kb = _build_offers_kb(slice_, 0, total_pages)
    await message.answer(text, parse_mode="Markdown", reply_markup=item_kb)


@router.callback_query(ProjectCallback.filter(F.action == ProjectAction.view_offer))
async def show_specific_offer(
    callback: types.CallbackQuery,
    callback_data: ProjectCallback,
    project_repo: ProjectRepository,
):
    proj_id = callback_data.id
    try:
        res = await GetOfferDetailService(project_repo).execute(proj_id, callback.from_user.id)
    except PermissionError as e:
        return await callback.answer(f"⚠️ {e}", show_alert=True)

    subject = escape_md(res["subject_name"])
    price = escape_md(res["price"])
    delivery = escape_md(res["delivery_date"])
    text = MSG_OFFER_DETAILS.format(subject, price, delivery, escape_md(proj_id))
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=get_offer_actions_kb(proj_id))


# ── CLOSE ACTIONS ────────────────────────────────────────────────────────
@router.callback_query(MenuCallback.filter(F.action == MenuAction.close_list))
async def cb_close_list(callback: types.CallbackQuery):
    try:
        from keyboards.common_kb import get_student_main_kb
        from utils.constants import MSG_WELCOME
        await callback.message.edit_text(MSG_WELCOME, parse_mode="Markdown", reply_markup=get_student_main_kb())
    except Exception:
        pass
    await callback.answer()
