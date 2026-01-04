from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from config import ADMIN_ID
from states import ProjectOrder
from database import add_project, get_user_projects
from utils.formatters import format_student_projects, format_admin_notification

router = Router()

# --- PROJECT SUBMISSION FLOW (FSM) ---

@router.message(Command("new_project"))
async def start_project(message: types.Message, state: FSMContext):
    await message.answer(
        "📚 What is the **Subject Name**?\n\n"
        "💡 *Tip: You can type /cancel at any time to stop.*"
    )
    await state.set_state(ProjectOrder.subject)

@router.message(ProjectOrder.subject)
async def process_subject(message: types.Message, state: FSMContext):
    await state.update_data(subject=message.text)
    await message.answer("👨‍🏫 What is the **Tutor's Name**?")
    await state.set_state(ProjectOrder.tutor)

@router.message(ProjectOrder.tutor)
async def process_tutor(message: types.Message, state: FSMContext):
    await state.update_data(tutor=message.text)
    await message.answer("📅 What is the **Final Date (Deadline)**?")
    await state.set_state(ProjectOrder.deadline)

@router.message(ProjectOrder.deadline)
async def process_deadline(message: types.Message, state: FSMContext):
    await state.update_data(deadline=message.text)
    await message.answer(
        "📝 Please send **Details**.\n"
        "You can type a description or upload a file (Image/PDF)."
    )
    await state.set_state(ProjectOrder.details)

@router.message(ProjectOrder.details)
async def process_details(message: types.Message, state: FSMContext, bot):
    data = await state.get_data()
    
    # Extract file_id and text
    file_id = message.document.file_id if message.document else (message.photo[-1].file_id if message.photo else None)
    details_text = message.text or message.caption or "No description provided."
    
    # Save to Database
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
        f"✅ **Project #{project_id} submitted!**\n"
        "The admin will review it and send you an offer shortly."
    )
    
    # Notify Admin (Using Formatter)
    admin_text = format_admin_notification(project_id, data['subject'], data['deadline'], details_text)
    await bot.send_message(ADMIN_ID, admin_text)
    await state.clear()

# --- PROJECT STATUS ---

@router.message(Command("my_projects"))
async def view_projects(message: types.Message):
    projects = get_user_projects(message.from_user.id)
    
    # Use the new student formatter
    response = format_student_projects(projects)
    await message.answer(response)