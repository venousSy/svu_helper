"""
Client Handler Module
Handles the student-facing Finite State Machine (FSM) for project submissions
and project status lookups.
"""

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from config import ADMIN_ID
from states import ProjectOrder
from database import add_project, get_user_projects

router = Router()

# --- PROJECT SUBMISSION FLOW (FSM) ---

@router.message(Command("new_project"))
async def start_project(message: types.Message, state: FSMContext):
    """Entry point for creating a new project request."""
    await message.answer(
        "📚 What is the **Subject Name**?\n\n"
        "💡 *Tip: You can type /cancel at any time to stop.*"
    )
    await state.set_state(ProjectOrder.subject)

@router.message(ProjectOrder.subject)
async def process_subject(message: types.Message, state: FSMContext):
    """Captures subject name and moves to tutor selection."""
    await state.update_data(subject=message.text)
    await message.answer("👨‍🏫 What is the **Tutor's Name**?")
    await state.set_state(ProjectOrder.tutor)

@router.message(ProjectOrder.tutor)
async def process_tutor(message: types.Message, state: FSMContext):
    """Captures tutor name and moves to deadline input."""
    await state.update_data(tutor=message.text)
    await message.answer("📅 What is the **Final Date (Deadline)**?")
    await state.set_state(ProjectOrder.deadline)

@router.message(ProjectOrder.deadline)
async def process_deadline(message: types.Message, state: FSMContext):
    """Captures deadline and requests final details/files."""
    await state.update_data(deadline=message.text)
    await message.answer(
        "📝 Please send **Details**.\n"
        "You can type a description or upload a file (Image/PDF)."
    )
    await state.set_state(ProjectOrder.details)

@router.message(ProjectOrder.details)
async def process_details(message: types.Message, state: FSMContext, bot):
    """
    Finalizes the project request. Handles text, images, and documents.
    Then, alerts the admin of the new request.
    """
    data = await state.get_data()
    
    # Extract file_id if a document or photo is provided
    file_id = None
    if message.document:
        file_id = message.document.file_id
    elif message.photo:
        file_id = message.photo[-1].file_id  # Get the highest resolution photo
        
    # Extract text from message or caption
    details_text = message.text or message.caption or "No description provided."
    
    # Save to Database via helper function
    project_id = add_project(
        user_id=message.from_user.id, 
        subject=data['subject'], 
        tutor=data['tutor'], 
        deadline=data['deadline'], 
        details=details_text, 
        file_id=file_id
    )

    # Confirm to Student
    await message.answer(
        f"✅ **Project #{project_id} submitted successfully!**\n"
        "The admin will review it and send you an offer shortly."
    )
    
    # Notify Admin
    await bot.send_message(
        ADMIN_ID, 
        f"🔔 **NEW PROJECT #{project_id}**\n"
        f"📚 Sub: {data['subject']}\n"
        f"📅 Deadline: {data['deadline']}\n"
        f"📝 Details: {details_text}"
    )
    await state.clear()

# --- PROJECT MANAGEMENT ---

@router.message(Command("my_projects"))
async def view_projects(message: types.Message):
    """Retrieves list of projects associated with the user's ID."""
    projects = get_user_projects(message.from_user.id)

    if not projects:
        await message.answer("📭 You haven't submitted any projects yet.")
        return

    response = "📋 **Your Project Status:**\n\n"
    for p_id, subject, status in projects:
        # Assign emoji based on status
        emoji = "⏳" if status == "Pending" else "✅" if status == "Accepted" else "❌"
        response += f"#{p_id} | {subject} - {emoji} {status}\n"
        
    await message.answer(response)