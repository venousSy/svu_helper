"""
Client Handler Module
=====================
Manages the student-facing Finite State Machine (FSM) for project submissions
and handles status inquiries for existing requests.
"""

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import ADMIN_ID
from states import ProjectOrder
from database import (
    add_project, 
    get_user_projects, 
    get_student_offers,
    get_project_by_id
)
from utils.formatters import (
    format_student_projects, 
    format_admin_notification, 
    format_offer_list,
    escape_md
)

from keyboards.client_kb import get_offer_actions_kb, get_offers_list_kb
from keyboards.admin_kb import get_new_project_alert_kb, get_payment_verify_kb
from utils.constants import (
    STATUS_OFFERED, 
    MSG_ASK_SUBJECT, MSG_ASK_TUTOR, MSG_ASK_DEADLINE, MSG_ASK_DETAILS, 
    MSG_NO_DESC, MSG_PROJECT_SUBMITTED, MSG_OFFER_ACCEPTED, 
    MSG_RECEIPT_RECEIVED, MSG_OFFER_DETAILS, MSG_NO_PROJECTS, MSG_NO_OFFERS
)

# Initialize router for student-related events
router = Router()

# --- PROJECT SUBMISSION FLOW (FSM) ---

@router.message(Command("new_project"))
async def start_project(message: types.Message, state: FSMContext):
    """
    Entry point for the project submission wizard.
    Initializes the FSM and requests the subject name.
    """
    """
    await message.answer(
        MSG_ASK_SUBJECT,
        parse_mode="Markdown"
    )
    await state.set_state(ProjectOrder.subject)

@router.message(ProjectOrder.subject)
async def process_subject(message: types.Message, state: FSMContext):
    """Stores the subject name and advances to tutor selection."""
    await state.update_data(subject=message.text)
    await message.answer(MSG_ASK_TUTOR, parse_mode="Markdown")
    await state.set_state(ProjectOrder.tutor)

@router.message(ProjectOrder.tutor)
async def process_tutor(message: types.Message, state: FSMContext):
    """Stores the tutor name and advances to deadline input."""
    await state.update_data(tutor=message.text)
    await message.answer(MSG_ASK_DEADLINE, parse_mode="Markdown")
    await state.set_state(ProjectOrder.deadline)

@router.message(ProjectOrder.deadline)
async def process_deadline(message: types.Message, state: FSMContext):
    """Stores the deadline and requests final project documentation/description."""
    await state.update_data(deadline=message.text)
    await message.answer(
        MSG_ASK_DETAILS,
        parse_mode="Markdown"
    )
    await state.set_state(ProjectOrder.details)

@router.message(ProjectOrder.details)
async def process_details(message: types.Message, state: FSMContext, bot):
    """
    Finalizes the FSM flow.
    Extracts media or text, saves to DB, and alerts the administrator.
    """
    # Retrieve all data collected during the FSM lifecycle
    data = await state.get_data()
    
    # Logic: Prioritize document, then photo. Fallback to None if text-only.
    file_id = None
    if message.document:
        file_id = message.document.file_id
    elif message.photo:
        file_id = message.photo[-1].file_id  # Select the highest resolution photo
    
    # Logic: Details can be in the message text or a file caption
    details_text = message.text or message.caption or MSG_NO_DESC
    
    # Capture user details
    user = message.from_user
    username = user.username  # Can be None
    full_name = user.full_name
    
    # Commit project to database and retrieve the auto-generated ID
    project_id = await add_project(
        user_id=user.id,
        username=username,
        user_full_name=full_name,
        subject=data['subject'], 
        tutor=data['tutor'], 
        deadline=data['deadline'], 
        details=details_text, 
        file_id=file_id
    )

    # Provide immediate feedback to the student
    await message.answer(
        MSG_PROJECT_SUBMITTED.format(project_id),
        parse_mode="Markdown"
    )
    
    admin_text = format_admin_notification(
        project_id, 
        data['subject'], 
        data['deadline'], 
        details_text,
        user_name=full_name,
        username=username
    )
    await bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown", reply_markup=get_new_project_alert_kb(project_id))
    
    # Clear FSM state to allow new commands
    await state.clear()


@router.callback_query(F.data.startswith("accept_"))
async def student_accept_offer(callback: types.CallbackQuery, state: FSMContext):
    """Student clicks 'Accept' on the offer."""
    proj_id = callback.data.split("_")[1]
    
    # Store the project ID in FSM so we know which project the receipt belongs to
    await state.update_data(active_pay_proj_id=proj_id)
    
    await callback.message.edit_text(
        MSG_OFFER_ACCEPTED.format(proj_id),
        parse_mode="Markdown"
    )
    # Set the state defined in your states.py
    await state.set_state(ProjectOrder.waiting_for_payment_proof)
    await callback.answer()

@router.message(ProjectOrder.waiting_for_payment_proof, F.photo | F.document)
async def process_payment_proof(message: types.Message, state: FSMContext, bot):
    """Student sends the receipt; we relay it to the Admin for verification."""
    data = await state.get_data()
    proj_id = data.get("active_pay_proj_id")
    
    # Identify the file
    file_id = message.photo[-1].file_id if message.photo else message.document.file_id
    
    # Notify Student
    await message.answer(MSG_RECEIPT_RECEIVED, parse_mode="Markdown")
    
    # Notify Admin
    await bot.send_message(ADMIN_ID, f"💰 **PAYMENT PROOF: Project #{proj_id}**", parse_mode="Markdown")
    await bot.send_photo(ADMIN_ID, file_id, caption=f"Verify payment for Project #{proj_id}", reply_markup=get_payment_verify_kb(proj_id))
    
    await state.clear()

# --- PROJECT STATUS LOOKUP ---

@router.message(Command("my_projects"))
async def view_projects(message: types.Message):
    """
    Retrieves and displays a list of all projects owned by the user.
    Uses centralized formatting for consistent UI/UX.
    """
    projects = await get_user_projects(message.from_user.id)
    
    # Generate the formatted response (handles empty lists internally)
    response = format_student_projects(projects)
    await message.answer(response, parse_mode="Markdown")


@router.message(Command("my_offers"))
async def view_offers(message: types.Message):
    """Shows the student all projects where an admin has sent an offer."""
    offers = await get_student_offers(message.from_user.id)
    text = format_offer_list(offers)
    
    # Use new keyboard
    markup = get_offers_list_kb(offers)
    
    await message.answer(text, parse_mode="Markdown", reply_markup=markup)

@router.callback_query(F.data.startswith("view_offer_"))
async def show_specific_offer(callback: types.CallbackQuery):
    proj_id = callback.data.split("_")[2]
    
    # Query the new columns!
    res = await get_project_by_id(proj_id)
    
    if res:
        subject = escape_md(res['subject_name'])
        price = escape_md(res['price'])
        delivery = escape_md(res['delivery_date'])
        
        text = MSG_OFFER_DETAILS.format(subject, price, delivery, proj_id)
        
        markup = get_offer_actions_kb(proj_id)
        
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=markup)