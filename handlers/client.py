"""
Client Handler Module
=====================
Manages the student-facing Finite State Machine (FSM) for project submissions
and handles status inquiries for existing requests.
"""

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from config import ADMIN_ID
from states import ProjectOrder
from database import add_project, get_user_projects
from utils.formatters import format_student_projects, format_admin_notification

# Initialize router for student-related events
router = Router()

# --- PROJECT SUBMISSION FLOW (FSM) ---

@router.message(Command("new_project"))
async def start_project(message: types.Message, state: FSMContext):
    """
    Entry point for the project submission wizard.
    Initializes the FSM and requests the subject name.
    """
    await message.answer(
        "📚 What is the **Subject Name**?\n\n"
        "💡 *Tip: You can type /cancel at any time to stop.*"
    )
    await state.set_state(ProjectOrder.subject)

@router.message(ProjectOrder.subject)
async def process_subject(message: types.Message, state: FSMContext):
    """Stores the subject name and advances to tutor selection."""
    await state.update_data(subject=message.text)
    await message.answer("👨‍🏫 What is the **Tutor's Name**?")
    await state.set_state(ProjectOrder.tutor)

@router.message(ProjectOrder.tutor)
async def process_tutor(message: types.Message, state: FSMContext):
    """Stores the tutor name and advances to deadline input."""
    await state.update_data(tutor=message.text)
    await message.answer("📅 What is the **Final Date (Deadline)**?")
    await state.set_state(ProjectOrder.deadline)

@router.message(ProjectOrder.deadline)
async def process_deadline(message: types.Message, state: FSMContext):
    """Stores the deadline and requests final project documentation/description."""
    await state.update_data(deadline=message.text)
    await message.answer(
        "📝 Please send **Details**.\n"
        "You can type a description or upload a file (Image/PDF)."
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
    details_text = message.text or message.caption or "No description provided."
    
    # Commit project to database and retrieve the auto-generated ID
    project_id = add_project(
        user_id=message.from_user.id, 
        subject=data['subject'], 
        tutor=data['tutor'], 
        deadline=data['deadline'], 
        details=details_text, 
        file_id=file_id
    )

    # Provide immediate feedback to the student
    await message.answer(
        f"✅ **Project #{project_id} submitted!**\n"
        "The admin will review it and send you an offer shortly."
    )
    
    # Notify Admin using the centralized notification formatter
    admin_text = format_admin_notification(
        project_id, 
        data['subject'], 
        data['deadline'], 
        details_text
    )
    await bot.send_message(ADMIN_ID, admin_text)
    
    # Clear FSM state to allow new commands
    await state.clear()

# --- PROJECT STATUS LOOKUP ---

@router.message(Command("my_projects"))
async def view_projects(message: types.Message):
    """
    Retrieves and displays a list of all projects owned by the user.
    Uses centralized formatting for consistent UI/UX.
    """
    projects = get_user_projects(message.from_user.id)
    
    # Generate the formatted response (handles empty lists internally)
    response = format_student_projects(projects)
    await message.answer(response)