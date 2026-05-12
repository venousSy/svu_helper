"""
Peer Routes
===========
Handles the "Virtual Island" Peer-Link Module interactions:
- Academic Profiling
- Creating / Searching Ads
- Secure Handshake Match Requests
"""
import structlog
from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from application.peer_service import PeerService
from keyboards.callbacks import MenuAction, MenuCallback, PeerAction, PeerCallback
from keyboards.factory import KeyboardFactory
from states import PeerProfileStates, PeerAdStates, PeerSearchStates
from utils.constants import (
    MSG_PEER_MENU,
    MSG_ASK_PROGRAM,
    MSG_ASK_SEMESTER,
    MSG_ASK_COURSES,
    MSG_PROFILE_UPDATED,
    MSG_ASK_AD_COURSE,
    MSG_ASK_AD_REQUIREMENTS,
    MSG_ASK_AD_DURATION,
    MSG_INVALID_DURATION,
    MSG_MAX_ADS_REACHED,
    MSG_AD_CREATED,
    MSG_ASK_SEARCH_COURSE,
    MSG_NO_ADS_FOUND,
    MSG_MATCH_ALREADY_PENDING,
    MSG_MATCH_REQUESTED,
    MSG_MATCH_REQUEST_RECEIVED,
    MSG_MATCH_ACCEPTED,
    MSG_MATCH_REJECTED,
)

logger = structlog.get_logger(__name__)
router = Router()


# ---------------------------------------------------------------------------
# Menu Navigation
# ---------------------------------------------------------------------------

@router.callback_query(MenuCallback.filter(F.action == MenuAction.peer_link))
async def show_peer_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        text=MSG_PEER_MENU,
        reply_markup=KeyboardFactory.peer_menu(),
        parse_mode="Markdown"
    )
    await callback.answer()


# ---------------------------------------------------------------------------
# 1. Academic Profiling
# ---------------------------------------------------------------------------

@router.callback_query(PeerCallback.filter(F.action == PeerAction.profile))
async def start_profiling(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(PeerProfileStates.waiting_for_program)
    await callback.message.edit_text(
        text=MSG_ASK_PROGRAM,
        reply_markup=KeyboardFactory.inline_cancel()
    )
    await callback.answer()

@router.message(PeerProfileStates.waiting_for_program, F.text)
async def process_program(message: types.Message, state: FSMContext):
    await state.update_data(program=message.text.strip())
    await state.set_state(PeerProfileStates.waiting_for_semester)
    await message.answer(MSG_ASK_SEMESTER, reply_markup=KeyboardFactory.inline_cancel())

@router.message(PeerProfileStates.waiting_for_semester, F.text)
async def process_semester(message: types.Message, state: FSMContext):
    await state.update_data(semester=message.text.strip())
    await state.set_state(PeerProfileStates.waiting_for_courses)
    await message.answer(MSG_ASK_COURSES, reply_markup=KeyboardFactory.inline_cancel())

@router.message(PeerProfileStates.waiting_for_courses, F.text)
async def process_courses(message: types.Message, state: FSMContext, peer_service: PeerService):
    courses = [c.strip().upper() for c in message.text.split()]
    data = await state.get_data()
    
    await peer_service.update_student_profile(
        user_id=message.from_user.id,
        program=data.get("program"),
        current_semester=data.get("semester"),
        enrolled_courses=courses
    )
    
    await state.clear()
    await message.answer(
        text=MSG_PROFILE_UPDATED,
        reply_markup=KeyboardFactory.peer_menu()
    )


# ---------------------------------------------------------------------------
# 2. Creating an Ad
# ---------------------------------------------------------------------------

@router.callback_query(PeerCallback.filter(F.action == PeerAction.post_ad))
async def start_post_ad(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(PeerAdStates.waiting_for_course_code)
    await callback.message.edit_text(
        text=MSG_ASK_AD_COURSE,
        reply_markup=KeyboardFactory.inline_cancel()
    )
    await callback.answer()

@router.message(PeerAdStates.waiting_for_course_code, F.text)
async def process_ad_course(message: types.Message, state: FSMContext):
    await state.update_data(course_code=message.text.strip().upper())
    await state.set_state(PeerAdStates.waiting_for_requirements)
    await message.answer(MSG_ASK_AD_REQUIREMENTS, reply_markup=KeyboardFactory.inline_cancel())

@router.message(PeerAdStates.waiting_for_requirements, F.text)
async def process_ad_requirements(message: types.Message, state: FSMContext):
    await state.update_data(requirements=message.text.strip())
    await state.set_state(PeerAdStates.waiting_for_duration)
    await message.answer(MSG_ASK_AD_DURATION, reply_markup=KeyboardFactory.inline_cancel())

@router.message(PeerAdStates.waiting_for_duration, F.text)
async def process_ad_duration(message: types.Message, state: FSMContext, peer_service: PeerService):
    try:
        duration = int(message.text.strip())
        if duration <= 0:
            raise ValueError()
    except ValueError:
        return await message.answer(MSG_INVALID_DURATION, reply_markup=KeyboardFactory.inline_cancel())
        
    data = await state.get_data()
    
    try:
        ad = await peer_service.create_project_ad(
            author_user_id=message.from_user.id,
            course_code=data.get("course_code"),
            requirements_text=data.get("requirements"),
            duration_hours=duration
        )
        duration_clamped = min(duration, 36)
        text = MSG_AD_CREATED.format(duration_clamped)
        
    except ValueError as e:
        if str(e) == "MAX_ADS_REACHED":
            text = MSG_MAX_ADS_REACHED
        else:
            text = f"⚠️ {e}"
            
    await state.clear()
    await message.answer(text, reply_markup=KeyboardFactory.peer_menu())


# ---------------------------------------------------------------------------
# 3. Searching Ads
# ---------------------------------------------------------------------------

@router.callback_query(PeerCallback.filter(F.action == PeerAction.search_ads))
async def start_search_ads(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(PeerSearchStates.waiting_for_search_course)
    await callback.message.edit_text(
        text=MSG_ASK_SEARCH_COURSE,
        reply_markup=KeyboardFactory.inline_cancel()
    )
    await callback.answer()

@router.message(PeerSearchStates.waiting_for_search_course, F.text)
async def process_search_course(message: types.Message, state: FSMContext, peer_service: PeerService):
    course_code = message.text.strip().upper()
    await state.clear()
    
    ads = await peer_service.search_active_ads(course_code=course_code, skip_user_id=message.from_user.id)
    
    if not ads:
        await message.answer(MSG_NO_ADS_FOUND, reply_markup=KeyboardFactory.peer_menu())
        return
        
    await message.answer(f"🔍 إعلانات المقرر {course_code}:")
    for ad in ads:
        text = f"📝 **{ad.course_code}**\n\n{ad.requirements_text}"
        await message.answer(text, reply_markup=KeyboardFactory.ad_actions(ad.ad_id), parse_mode="Markdown")


# ---------------------------------------------------------------------------
# 4. Secure Handshake (Match Requests)
# ---------------------------------------------------------------------------

@router.callback_query(PeerCallback.filter(F.action == PeerAction.request_match))
async def request_match_cb(callback: types.CallbackQuery, callback_data: PeerCallback, peer_service: PeerService):
    ad_id = callback_data.id
    
    try:
        request = await peer_service.send_match_request(
            requester_user_id=callback.from_user.id,
            ad_id=ad_id
        )
        
        # Notify the ad owner
        owner_id = request.owner_user_id
        text_for_owner = MSG_MATCH_REQUEST_RECEIVED.format(ad_id) # Should format with course_code if available, but ad_id is fine or get from db.
        
        from main import bot # Import bot to send message
        try:
            await bot.send_message(
                chat_id=owner_id,
                text=text_for_owner,
                reply_markup=KeyboardFactory.match_request_actions(request.request_id),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error("failed_to_notify_owner", error=str(e))
            
        await callback.answer(MSG_MATCH_REQUESTED, show_alert=True)
        
    except ValueError as e:
        if str(e) == "REQUEST_ALREADY_PENDING":
            await callback.answer(MSG_MATCH_ALREADY_PENDING, show_alert=True)
        else:
            await callback.answer(f"⚠️ {e}", show_alert=True)

@router.callback_query(PeerCallback.filter(F.action == PeerAction.accept_match))
async def accept_match_cb(callback: types.CallbackQuery, callback_data: PeerCallback, peer_service: PeerService):
    request_id = callback_data.id
    success, request = await peer_service.respond_to_match(
        request_id=request_id,
        owner_user_id=callback.from_user.id,
        accept=True
    )
    
    if not success or not request:
        return await callback.answer("❌ تعذر إتمام العملية.", show_alert=True)
        
    requester_id = request.requester_user_id
    
    from main import bot
    try:
        # Get requester's info to send to owner
        requester_chat = await bot.get_chat(requester_id)
        requester_handle = requester_chat.username or str(requester_id)
        
        # Get owner's info to send to requester
        owner_handle = callback.from_user.username or str(callback.from_user.id)
        
        # Notify Requester
        await bot.send_message(
            chat_id=requester_id,
            text=MSG_MATCH_ACCEPTED.format(owner_handle)
        )
        
        # Edit message for Owner
        await callback.message.edit_text(
            text=MSG_MATCH_ACCEPTED.format(requester_handle)
        )
    except Exception as e:
        logger.error("failed_to_exchange_contacts", error=str(e))
        
    await callback.answer()

@router.callback_query(PeerCallback.filter(F.action == PeerAction.reject_match))
async def reject_match_cb(callback: types.CallbackQuery, callback_data: PeerCallback, peer_service: PeerService):
    request_id = callback_data.id
    success, request = await peer_service.respond_to_match(
        request_id=request_id,
        owner_user_id=callback.from_user.id,
        accept=False
    )
    
    if not success or not request:
        return await callback.answer("❌ تعذر إتمام العملية.", show_alert=True)
        
    from main import bot
    try:
        # Notify Requester
        await bot.send_message(
            chat_id=request.requester_user_id,
            text=MSG_MATCH_REJECTED
        )
    except Exception:
        pass
        
    await callback.message.edit_text(text="❌ تم الرفض.")
    await callback.answer()
