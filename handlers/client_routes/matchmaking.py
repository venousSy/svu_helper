"""
Client Routes – Matchmaking
===========================
Handlers for student team matchmaking flow:
- Creating a team request (Host)
- Finding a team to join (Seeker)
- Responding to join requests (Host)
"""
from typing import Any, Dict
import structlog
from aiogram import F, Router, types, Bot
from aiogram.fsm.context import FSMContext

from application.matchmaking_service import (
    CreateTeamRequestService,
    FindOpenTeamsService,
    JoinTeamService,
    HandleJoinDecisionService,
)
from infrastructure.repositories import TeamRequestRepository
from keyboards.callbacks import MenuAction, MenuCallback, TeamAction, TeamCallback
from keyboards.factory import KeyboardFactory
from states import TeamStates
from utils.constants import (
    MSG_TEAM_MENU_HEADER,
    MSG_TEAM_CHOOSE_COURSE,
    MSG_TEAM_CHOOSE_COUNT,
    MSG_TEAM_CREATED,
    MSG_TEAM_NO_OPEN,
    MSG_TEAM_CARD,
    MSG_TEAM_JOIN_SENT,
    MSG_TEAM_JOIN_DUPLICATE,
    MSG_TEAM_JOIN_OWN,
    MSG_TEAM_JOIN_CLOSED,
    MSG_TEAM_HOST_NOTIFICATION,
    MSG_TEAM_JOIN_ACCEPTED_HOST,
    MSG_TEAM_JOIN_ACCEPTED_SEEKER,
    MSG_TEAM_JOIN_REJECTED_SEEKER,
    MSG_TEAM_FULL,
    MSG_TEAM_NO_MY_TEAMS,
    MSG_TEAM_MY_HEADER,
    MSG_TEAM_NO_COMPLETED_TEAMS,
    MSG_TEAM_MY_COMPLETED_HEADER,
)
from utils.courses import get_all_courses

logger = structlog.get_logger(__name__)
router = Router()

def parse_team_callback(data_str: str) -> tuple[str, int, str]:
    """Parse team callback data cleanly without relying on CallbackData unpack.
    Returns: (action, request_id, extra_data)
    """
    parts = data_str.split(":")
    action = parts[1] if len(parts) > 1 else ""
    req_id = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
    extra = parts[3] if len(parts) > 3 else ""
    return action, req_id, extra


# --- Main Menu & Navigation ---

@router.callback_query(MenuCallback.filter(F.action == MenuAction.teams))
async def on_team_menu(
    callback: types.CallbackQuery,
    state: FSMContext,
) -> None:
    """Show the main matchmaking menu."""
    logger.info("Opened team menu", user_id=callback.from_user.id)
    await state.clear()
    await callback.message.edit_text(
        text=MSG_TEAM_MENU_HEADER,
        reply_markup=KeyboardFactory.team_main_menu(),
    )
    await callback.answer()


# --- Host Flow: Create Team ---

@router.callback_query(F.data.startswith("team:create"))
async def start_team_creation(
    callback: types.CallbackQuery,
    state: FSMContext,
) -> None:
    """Step 1: Ask host to choose a course."""
    logger.info("Starting team creation", user_id=callback.from_user.id)
    courses = get_all_courses()
    await state.set_state(TeamStates.choosing_course)
    await callback.message.edit_text(
        text=MSG_TEAM_CHOOSE_COURSE,
        reply_markup=KeyboardFactory.team_course_selection(courses),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("team:sel_course"), TeamStates.choosing_course)
async def process_course_selection(
    callback: types.CallbackQuery,
    state: FSMContext,
) -> None:
    """Save chosen course and ask for team member count."""
    _, _, course_name = parse_team_callback(callback.data)
    await state.update_data(course_name=course_name)
    await state.set_state(TeamStates.choosing_member_count)
    await callback.message.edit_text(
        text=MSG_TEAM_CHOOSE_COUNT,
        reply_markup=KeyboardFactory.team_count_selection(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("team:sel_count"), TeamStates.choosing_member_count)
async def process_count_selection(
    callback: types.CallbackQuery,
    state: FSMContext,
    team_request_repo: TeamRequestRepository,
) -> None:
    """Save count, finalize team creation, and save to DB."""
    _, _, count_str = parse_team_callback(callback.data)
    required_members = int(count_str) if count_str.isdigit() else 3

    data = await state.get_data()
    course_name = data["course_name"]

    user = callback.from_user
    service = CreateTeamRequestService(team_request_repo)
    
    try:
        request_id = await service.execute(
            host_id=user.id,
            host_name=user.full_name,
            host_username=user.username,
            course_name=course_name,
            required_members=required_members,
        )
        
        await state.clear()
        await callback.message.edit_text(
            text=MSG_TEAM_CREATED.format(request_id, course_name, required_members),
            reply_markup=KeyboardFactory.inline_cancel()
        )
    except ValueError as e:
        err_msg = str(e)
        if err_msg == "already_host_for_course":
            await callback.answer("لديك بالفعل طلب فريق مفتوح لهذه المادة.", show_alert=True)
        else:
            await callback.answer(err_msg, show_alert=True)
    await callback.answer()


# --- Host Flow: View My Open Teams ---

@router.callback_query(F.data.startswith("team:my_teams"))
async def view_my_teams(
    callback: types.CallbackQuery,
    team_request_repo: TeamRequestRepository,
) -> None:
    """Show the host's open teams."""
    teams = await team_request_repo.get_user_open_requests(callback.from_user.id)
    if not teams:
        await callback.answer(MSG_TEAM_NO_MY_TEAMS, show_alert=True)
        return

    # For simplicity, we just send a message for each open team.
    # In a real app, this might be paginated.
    await callback.message.edit_text(
        text=MSG_TEAM_MY_HEADER,
        reply_markup=KeyboardFactory.inline_cancel()
    )
    
    for t in teams:
        text = MSG_TEAM_CARD.format(
            t["id"],
            t.get("host_name", "Unknown"),
            t["course_name"],
            len(t["current_members"]),
            t["required_members"],
        )
        await callback.message.answer(text)
    await callback.answer()

@router.callback_query(F.data.startswith("team:my_cmp_teams"))
async def view_my_completed_teams(
    callback: types.CallbackQuery,
    team_request_repo: TeamRequestRepository,
) -> None:
    """Show the user's completed teams (either as host or member)."""
    teams = await team_request_repo.get_user_completed_requests(callback.from_user.id)
    if not teams:
        await callback.answer(MSG_TEAM_NO_COMPLETED_TEAMS, show_alert=True)
        return

    await callback.message.edit_text(
        text=MSG_TEAM_MY_COMPLETED_HEADER,
        reply_markup=KeyboardFactory.inline_cancel()
    )
    
    for t in teams:
        text = MSG_TEAM_CARD.format(
            t["id"],
            t.get("host_name", "Unknown"),
            t["course_name"],
            len(t["current_members"]),
            t["required_members"],
        )
        await callback.message.answer(text)
    await callback.answer()


@router.callback_query(F.data.startswith("team:find"))
async def find_teams(
    callback: types.CallbackQuery,
    team_request_repo: TeamRequestRepository,
) -> None:
    """Find open teams matching the seeker's courses."""
    courses = get_all_courses()
    
    service = FindOpenTeamsService(team_request_repo)
    open_teams = await service.execute(courses, callback.from_user.id)

    if not open_teams:
        await callback.message.edit_text(
            text=MSG_TEAM_NO_OPEN,
            reply_markup=KeyboardFactory.inline_cancel()
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        text="🔍 فرق متاحة:",
        reply_markup=KeyboardFactory.inline_cancel()
    )

    for t in open_teams:
        card_text = MSG_TEAM_CARD.format(
            t["id"],
            t.get("host_name", "Unknown"),
            t["course_name"],
            len(t["current_members"]),
            t["required_members"],
        )
        await callback.message.answer(
            text=card_text,
            reply_markup=KeyboardFactory.team_join_action(t["id"])
        )
    await callback.answer()

# --- Seeker Flow: Join Team ---

@router.callback_query(F.data.startswith("team:join"))
async def join_team(
    callback: types.CallbackQuery,
    team_request_repo: TeamRequestRepository,
    bot: Bot,
) -> None:
    """Process seeker's request to join a specific team."""
    _, request_id, _ = parse_team_callback(callback.data)
    seeker = callback.from_user

    service = JoinTeamService(team_request_repo)
    try:
        team = await service.execute(
            request_id=request_id,
            seeker_id=seeker.id,
            seeker_name=seeker.full_name,
        )
        
        await callback.answer(MSG_TEAM_JOIN_SENT, show_alert=True)

        # Notify host
        host_msg = MSG_TEAM_HOST_NOTIFICATION.format(
            seeker.full_name,
            request_id,
            team["course_name"]
        )
        await bot.send_message(
            chat_id=team["host_id"],
            text=host_msg,
            reply_markup=KeyboardFactory.team_host_join_decision(request_id, seeker.id)
        )

    except ValueError as e:
        err_key = str(e)
        if err_key == "duplicate":
            await callback.answer(MSG_TEAM_JOIN_DUPLICATE, show_alert=True)
        elif err_key == "own_team":
            await callback.answer(MSG_TEAM_JOIN_OWN, show_alert=True)
        elif err_key == "closed":
            await callback.answer(MSG_TEAM_JOIN_CLOSED, show_alert=True)
        elif err_key == "already_member":
            await callback.answer("أنت عضو في هذا الفريق بالفعل.", show_alert=True)
        else:
            await callback.answer("Error processing join request.", show_alert=True)


# --- Host Flow: Decide Join Request ---

@router.callback_query(F.data.startswith("team:acc_join") | F.data.startswith("team:rej_join"))
async def host_join_decision(
    callback: types.CallbackQuery,
    team_request_repo: TeamRequestRepository,
    bot: Bot,
) -> None:
    """Process host's decision to accept or reject a join request."""
    action, request_id, extra = parse_team_callback(callback.data)
    seeker_id = int(extra) if extra.isdigit() else 0
    
    service = HandleJoinDecisionService(team_request_repo)

    if action == "acc_join":
        try:
            res = await service.accept(request_id, seeker_id)
        except ValueError as e:
            if str(e) == "team_full":
                await callback.answer("الفريق ممتلئ بالفعل!", show_alert=True)
            else:
                await callback.answer(str(e), show_alert=True)
            return

        team = res["team"]
        is_full = res["is_full"]
        
        seeker_name = str(seeker_id)
        for req in team["join_requests"]:
            if req["seeker_id"] == seeker_id:
                seeker_name = req.get("seeker_name") or str(seeker_id)
                break

        seeker_contact = f"<a href='tg://user?id={seeker_id}'>حساب الطالب</a>"
        host_contact = f"<a href='tg://user?id={team['host_id']}'>حساب المنشئ</a>"

        # Notify host
        await callback.message.edit_text(
            MSG_TEAM_JOIN_ACCEPTED_HOST.format(
                seeker_name,
                request_id,
                len(team["current_members"]),
                team["required_members"],
                seeker_contact
            ),
            parse_mode="HTML"
        )
        
        # Notify seeker
        await callback.bot.send_message(
            chat_id=seeker_id,
            text=MSG_TEAM_JOIN_ACCEPTED_SEEKER.format(
                request_id,
                team["course_name"],
                host_contact
            ),
            parse_mode="HTML"
        )

        if is_full:
            await callback.message.answer(
                MSG_TEAM_FULL.format(request_id, team["course_name"])
            )
        await callback.answer()

    else:
        team = await service.reject(request_id, seeker_id)
        await callback.message.edit_text(f"❌ تم رفض الطلب من {seeker_id}")
        
        # Notify seeker
        await callback.bot.send_message(
            chat_id=seeker_id,
            text=MSG_TEAM_JOIN_REJECTED_SEEKER.format(request_id, team["course_name"])
        )
        await callback.answer()
