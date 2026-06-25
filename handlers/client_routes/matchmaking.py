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
    ManageTeamService,
)
from infrastructure.repositories import TeamRequestRepository, StudentRepository
from keyboards.callbacks import MenuAction, MenuCallback, TeamAction, TeamCallback, ProfileCallback, PageAction, PageCallback
from keyboards.factory import KeyboardFactory
from states import TeamStates, ProfileStates
from utils.constants import (
    MSG_TEAM_MENU_HEADER,
    MSG_TEAM_CHOOSE_COUNT,
    MSG_TEAM_CREATED,
    MSG_TEAM_NO_OPEN,
    MSG_TEAM_CARD,
    MSG_TEAM_JOIN_SENT,
    MSG_TEAM_JOIN_DUPLICATE,
    MSG_TEAM_JOIN_OWN,
    MSG_TEAM_JOIN_CLOSED,
    MSG_TEAM_ALREADY_MEMBER,
    MSG_TEAM_JOIN_ERROR,
    MSG_TEAM_HOST_NOTIFICATION,
    MSG_TEAM_JOIN_ACCEPTED_HOST,
    MSG_TEAM_JOIN_ACCEPTED_SEEKER,
    MSG_TEAM_JOIN_REJECTED_SEEKER,
    MSG_TEAM_FULL,
    MSG_TEAM_NO_MY_TEAMS,
    MSG_TEAM_MY_HEADER,
    MSG_TEAM_NO_COMPLETED_TEAMS,
    MSG_TEAM_MY_COMPLETED_HEADER,
    MSG_TEAM_CHOOSE_SPECIALIZATION,
    MSG_TEAM_PROFILE_SAVED,
    MSG_TEAM_ENTER_COURSE_NAME,
    MSG_TEAM_ENTER_DOCTOR_NAME,
    MSG_TEAM_CREATION_EXISTS,
    MSG_TEAM_NO_PENDING_JOINS,
    MSG_TEAM_PENDING_JOINS_HEADER,
    MSG_TEAM_ACTIVE_INVOLVEMENT_EXISTS,
    MSG_TEAM_CLOSED_EARLY,
    MSG_TEAM_DELETED,
    MSG_TEAM_JOIN_WITHDRAWN,
)
from utils.specializations import get_all_specializations
from utils.pagination import paginate

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
    student_repo: StudentRepository,
) -> None:
    """Show the main matchmaking menu."""
    logger.info("Opened team menu", user_id=callback.from_user.id)
    await state.clear()
    
    # Check if student has a profile
    profile = await student_repo.get_profile(callback.from_user.id)
    if not profile:
        specs = await get_all_specializations()
        await state.set_state(ProfileStates.choosing_specialization)
        await callback.message.edit_text(
            text=MSG_TEAM_CHOOSE_SPECIALIZATION,
            reply_markup=KeyboardFactory.specialization_selection(specs)
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        text=MSG_TEAM_MENU_HEADER,
        reply_markup=KeyboardFactory.team_main_menu(),
    )
    await callback.answer()


@router.callback_query(ProfileCallback.filter(F.action == "select_spec"), ProfileStates.choosing_specialization)
async def process_specialization_selection(
    callback: types.CallbackQuery,
    callback_data: ProfileCallback,
    state: FSMContext,
    student_repo: StudentRepository,
) -> None:
    """Save chosen specialization and show team menu."""
    await student_repo.create_profile(callback.from_user.id, callback_data.spec)
    await state.clear()
    await callback.message.edit_text(
        text=f"{MSG_TEAM_PROFILE_SAVED}\n\n{MSG_TEAM_MENU_HEADER}",
        reply_markup=KeyboardFactory.team_main_menu(),
    )
    await callback.answer()


# --- Host Flow: Create Team ---

@router.callback_query(F.data.startswith("team:create"))
async def start_team_creation(
    callback: types.CallbackQuery,
    state: FSMContext,
) -> None:
    """Step 1: Ask host to type course name."""
    logger.info("Starting team creation", user_id=callback.from_user.id)
    await state.set_state(TeamStates.typing_course_name)
    await callback.message.edit_text(
        text=MSG_TEAM_ENTER_COURSE_NAME,
        reply_markup=KeyboardFactory.inline_cancel(),
    )
    await callback.answer()


@router.message(TeamStates.typing_course_name)
async def process_course_name(
    message: types.Message,
    state: FSMContext,
) -> None:
    """Save course name and ask for doctor name."""
    course_name = message.text.strip()
    await state.update_data(course_name=course_name)
    await state.set_state(TeamStates.typing_doctor_name)
    await message.answer(
        text=MSG_TEAM_ENTER_DOCTOR_NAME,
        reply_markup=KeyboardFactory.inline_cancel(),
    )


@router.message(TeamStates.typing_doctor_name)
async def process_doctor_name(
    message: types.Message,
    state: FSMContext,
) -> None:
    """Save doctor name and ask for team member count."""
    doctor_name = message.text.strip()
    await state.update_data(doctor_name=doctor_name)
    await state.set_state(TeamStates.choosing_member_count)
    await message.answer(
        text=MSG_TEAM_CHOOSE_COUNT,
        reply_markup=KeyboardFactory.team_count_selection(),
    )


@router.callback_query(F.data.startswith("team:sel_count"), TeamStates.choosing_member_count)
async def process_count_selection(
    callback: types.CallbackQuery,
    state: FSMContext,
    team_request_repo: TeamRequestRepository,
    student_repo: StudentRepository,
) -> None:
    """Save count, finalize team creation, and save to DB."""
    _, _, count_str = parse_team_callback(callback.data)
    required_members = int(count_str) if count_str.isdigit() else 3

    data = await state.get_data()
    course_name = data["course_name"]
    doctor_name = data["doctor_name"]

    user = callback.from_user
    profile = await student_repo.get_profile(user.id)
    specialization = profile.specialization if profile else "Unknown"

    service = CreateTeamRequestService(team_request_repo)
    
    try:
        request_id = await service.execute(
            host_id=user.id,
            host_name=user.full_name,
            host_username=user.username,
            course_name=course_name,
            doctor_name=doctor_name,
            specialization=specialization,
            required_members=required_members,
        )
        
        await state.clear()
        await callback.message.edit_text(
            text=MSG_TEAM_CREATED.format(request_id, course_name, required_members),
            reply_markup=KeyboardFactory.inline_cancel()
        )
    except ValueError as e:
        err_msg = str(e)
        if err_msg == "global_team_exists":
            await callback.answer(MSG_TEAM_CREATION_EXISTS, show_alert=True)
        elif err_msg == "active_involvement_exists":
            await callback.answer(MSG_TEAM_ACTIVE_INVOLVEMENT_EXISTS, show_alert=True)
        else:
            await callback.answer(err_msg, show_alert=True)
    await callback.answer()


# --- Host Flow: View My Open Teams ---

@router.callback_query(F.data.startswith("team:my_teams"))
@router.callback_query(PageCallback.filter(F.action == PageAction.my_teams))
async def view_my_teams(
    callback: types.CallbackQuery,
    team_request_repo: TeamRequestRepository,
    callback_data: Any = None,
) -> None:
    """Show the host's open teams using pagination."""
    teams = await team_request_repo.get_user_open_requests(callback.from_user.id)
    if not teams:
        if isinstance(callback_data, PageCallback):
            await callback.message.edit_text(MSG_TEAM_NO_MY_TEAMS, reply_markup=KeyboardFactory.team_main_menu())
        else:
            await callback.answer(MSG_TEAM_NO_MY_TEAMS, show_alert=True)
        return

    page = callback_data.page if isinstance(callback_data, PageCallback) else 0
    page_slice, total_pages, page = paginate(teams, page, 5)
    
    texts = []
    team_info = []
    for t in page_slice:
        team_info.append((t["id"], t["course_name"]))
        card_text = MSG_TEAM_CARD.format(
            t["id"],
            t.get("host_name", "Unknown"),
            t["course_name"],
            t.get("doctor_name", "غير محدد"),
            len(t["current_members"]),
            t["required_members"],
        )
        texts.append(card_text)

    combined_text = "\n\n➖➖➖➖➖➖\n\n".join(texts)

    await callback.message.edit_text(
        text=f"{MSG_TEAM_MY_HEADER}\n\n{combined_text}",
        reply_markup=KeyboardFactory.paginated_teams(
            PageAction.my_teams, page, total_pages, team_info=team_info, is_host=True
        )
    )
    if not isinstance(callback_data, PageCallback):
        await callback.answer()

@router.callback_query(F.data.startswith("team:my_cmp_teams"))
@router.callback_query(PageCallback.filter(F.action == PageAction.my_cmp_teams))
async def view_my_completed_teams(
    callback: types.CallbackQuery,
    team_request_repo: TeamRequestRepository,
    callback_data: Any = None,
) -> None:
    """Show the user's completed teams using pagination."""
    teams = await team_request_repo.get_user_completed_requests(callback.from_user.id)
    if not teams:
        if isinstance(callback_data, PageCallback):
            await callback.message.edit_text(MSG_TEAM_NO_COMPLETED_TEAMS, reply_markup=KeyboardFactory.team_main_menu())
        else:
            await callback.answer(MSG_TEAM_NO_COMPLETED_TEAMS, show_alert=True)
        return

    page = callback_data.page if isinstance(callback_data, PageCallback) else 0
    page_slice, total_pages, page = paginate(teams, page, 5)
    
    texts = []
    team_info = []
    for t in page_slice:
        team_info.append((t["id"], t["course_name"]))
        text = MSG_TEAM_CARD.format(
            t["id"],
            t.get("host_name", "Unknown"),
            t["course_name"],
            t.get("doctor_name", "غير محدد"),
            len(t["current_members"]),
            t["required_members"],
        )
        
        contacts = []
        host_username = t.get('host_username')
        host_link = f"<a href='tg://user?id={t['host_id']}'>{t.get('host_name', 'المنشئ')}</a> (المنشئ)"
        if host_username:
            host_link += f" - @{host_username}"
        contacts.append(host_link)
        
        for req in t.get("join_requests", []):
            if req.get("seeker_id") in t.get("current_members", []):
                s_name = req.get("seeker_name") or "عضو"
                s_id = req.get("seeker_id")
                s_username = req.get("seeker_username")
                member_link = f"<a href='tg://user?id={s_id}'>{s_name}</a>"
                if s_username:
                    member_link += f" - @{s_username}"
                contacts.append(member_link)
                
        text += "\n\n💬 <b>روابط التواصل مع الأعضاء:</b>\n" + "\n".join([f"▪️ {c}" for c in contacts])
        texts.append(text)

    combined_text = "\n\n➖➖➖➖➖➖\n\n".join(texts)
    
    await callback.message.edit_text(
        text=f"{MSG_TEAM_MY_COMPLETED_HEADER}\n\n{combined_text}",
        parse_mode="HTML",
        reply_markup=KeyboardFactory.paginated_teams(
            PageAction.my_cmp_teams, page, total_pages, team_info=team_info, is_completed=True
        )
    )
    if not isinstance(callback_data, PageCallback):
        await callback.answer()


@router.callback_query(F.data.startswith("team:find"))
@router.callback_query(PageCallback.filter(F.action == PageAction.find_teams))
async def find_teams(
    callback: types.CallbackQuery,
    team_request_repo: TeamRequestRepository,
    student_repo: StudentRepository,
    callback_data: Any = None,
) -> None:
    """Find open teams matching the seeker's specialization."""
    profile = await student_repo.get_profile(callback.from_user.id)
    if not profile:
        await callback.answer("Profile not found. Please click Teams menu again.", show_alert=True)
        return
    
    service = FindOpenTeamsService(team_request_repo)
    open_teams = await service.execute(profile.specialization, callback.from_user.id)

    if not open_teams:
        if isinstance(callback_data, PageCallback):
            await callback.message.edit_text(MSG_TEAM_NO_OPEN, reply_markup=KeyboardFactory.team_main_menu())
        else:
            await callback.answer(MSG_TEAM_NO_OPEN, show_alert=True)
        return

    page = callback_data.page if isinstance(callback_data, PageCallback) else 0
    page_slice, total_pages, page = paginate(open_teams, page, 5)
    
    texts = []
    team_info = []
    for t in page_slice:
        team_info.append((t["id"], t["course_name"]))
        card_text = MSG_TEAM_CARD.format(
            t["id"],
            t.get("host_name", "Unknown"),
            t["course_name"],
            t.get("doctor_name", "غير محدد"),
            len(t["current_members"]),
            t["required_members"],
        )
        texts.append(card_text)

    combined_text = "\n\n➖➖➖➖➖➖\n\n".join(texts)
    
    await callback.message.edit_text(
        text=f"🔍 فرق متاحة:\n\n{combined_text}",
        reply_markup=KeyboardFactory.paginated_teams(
            PageAction.find_teams, page, total_pages, team_info=team_info
        )
    )
    if not isinstance(callback_data, PageCallback):
        await callback.answer()

@router.callback_query(F.data.startswith("team:my_pend_joins"))
@router.callback_query(PageCallback.filter(F.action == PageAction.my_pending_joins))
async def view_my_pending_joins(
    callback: types.CallbackQuery,
    team_request_repo: TeamRequestRepository,
    callback_data: Any = None,
) -> None:
    """Show the seeker's pending join requests."""
    service = FindOpenTeamsService(team_request_repo)
    joins = await service.get_user_pending_joins(callback.from_user.id)
    
    if not joins:
        if isinstance(callback_data, PageCallback):
            await callback.message.edit_text(MSG_TEAM_NO_PENDING_JOINS, reply_markup=KeyboardFactory.team_main_menu())
        else:
            await callback.answer(MSG_TEAM_NO_PENDING_JOINS, show_alert=True)
        return

    page = callback_data.page if isinstance(callback_data, PageCallback) else 0
    page_slice, total_pages, page = paginate(joins, page, 5)
    
    texts = []
    team_info = []
    for t in page_slice:
        team_info.append((t["id"], t["course_name"]))
        card_text = MSG_TEAM_CARD.format(
            t["id"],
            t.get("host_name", "Unknown"),
            t["course_name"],
            t.get("doctor_name", "غير محدد"),
            len(t["current_members"]),
            t["required_members"],
        )
        texts.append(card_text)

    combined_text = "\n\n➖➖➖➖➖➖\n\n".join(texts)

    await callback.message.edit_text(
        text=f"{MSG_TEAM_PENDING_JOINS_HEADER}\n\n{combined_text}",
        reply_markup=KeyboardFactory.paginated_teams(
            PageAction.my_pending_joins, page, total_pages, team_info=team_info, is_pending=True
        )
    )
    if not isinstance(callback_data, PageCallback):
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
            await callback.answer(MSG_TEAM_ALREADY_MEMBER, show_alert=True)
        else:
            await callback.answer(MSG_TEAM_JOIN_ERROR, show_alert=True)


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
        await _handle_accept_join(callback, request_id, seeker_id, service)
    else:
        await _handle_reject_join(callback, request_id, seeker_id, service)


async def _handle_accept_join(callback, request_id, seeker_id, service):
    try:
        res = await service.accept(request_id, seeker_id)
    except ValueError as e:
        if str(e) == "team_full":
            await callback.answer(MSG_TEAM_FULL, show_alert=True)
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
        # Note: In Python, string format expecting 2 args must be passed 2 args. 
        # The translation for team_full doesn't use formatting, but maybe MSG_TEAM_FULL is misused here.
        # Actually MSG_TEAM_FULL in original code was `MSG_TEAM_FULL.format(request_id, team["course_name"])` but the translation I added had no `{}`. 
        # I'll just use the constant without format here, as it was in my translation.
        await callback.message.answer(MSG_TEAM_FULL)
    await callback.answer()


async def _handle_reject_join(callback, request_id, seeker_id, service):
    team = await service.reject(request_id, seeker_id)
    await callback.message.edit_text(f"❌ تم رفض الطلب من {seeker_id}")
    
    # Notify seeker
    await callback.bot.send_message(
        chat_id=seeker_id,
        text=MSG_TEAM_JOIN_REJECTED_SEEKER.format(request_id, team["course_name"])
    )
    await callback.answer()

# --- Management Flow ---

@router.callback_query(F.data.startswith("team:close"))
async def host_close_team(
    callback: types.CallbackQuery,
    team_request_repo: TeamRequestRepository,
) -> None:
    """Host closes their team early."""
    _, request_id, _ = parse_team_callback(callback.data)
    service = ManageTeamService(team_request_repo)
    try:
        await service.close_team(request_id, callback.from_user.id)
        await callback.message.edit_text(MSG_TEAM_CLOSED_EARLY)
    except ValueError as e:
        await callback.answer(str(e), show_alert=True)

@router.callback_query(F.data.startswith("team:delete"))
async def host_delete_team(
    callback: types.CallbackQuery,
    team_request_repo: TeamRequestRepository,
) -> None:
    """Host deletes their team request."""
    _, request_id, _ = parse_team_callback(callback.data)
    service = ManageTeamService(team_request_repo)
    try:
        await service.delete_team(request_id, callback.from_user.id)
        await callback.message.edit_text(MSG_TEAM_DELETED)
    except ValueError as e:
        await callback.answer(str(e), show_alert=True)

@router.callback_query(F.data.startswith("team:withdraw"))
async def seeker_withdraw_join(
    callback: types.CallbackQuery,
    team_request_repo: TeamRequestRepository,
) -> None:
    """Seeker withdraws their join request."""
    _, request_id, _ = parse_team_callback(callback.data)
    service = ManageTeamService(team_request_repo)
    try:
        await service.withdraw_join(request_id, callback.from_user.id)
        await callback.message.edit_text(MSG_TEAM_JOIN_WITHDRAWN)
    except ValueError as e:
        await callback.answer(str(e), show_alert=True)

