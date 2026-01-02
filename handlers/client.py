from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from config import ADMIN_ID
from states import ProjectOrder
from database import add_project, get_user_projects
router = Router()

@router.message(Command("new_project"))
async def start_project(message: types.Message, state: FSMContext):
    await message.answer("📚 What is the **Subject Name**?")
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
    await message.answer("📝 Please send **Details** (Type text or upload a PDF/Image).")
    await state.set_state(ProjectOrder.details)

@router.message(ProjectOrder.details)
async def process_details(message: types.Message, state: FSMContext, bot):
    data = await state.get_data()
    file_id = message.document.file_id if message.document else None
    details_text = message.caption if message.document else message.text
    
    project_id = add_project(
        user_id=message.from_user.id, 
        subject=data['subject'], 
        tutor=data['tutor'], 
        deadline=data['deadline'], 
        details=details_text, 
        file_id=file_id
    )

    await message.answer(f"✅ Project #{project_id} submitted!")
    await bot.send_message(ADMIN_ID, f"🔔 **NEW PROJECT #{project_id}**\nSub: {data['subject']}\nDetails: {details_text}")
    await state.clear()

@router.message(Command("my_projects"))
async def view_projects(message: types.Message):
    projects = get_user_projects(message.from_user.id)

    if not projects:
        await message.answer("📭 You haven't submitted any projects yet.")
        return

    response = "📋 **Your Projects:**\n\n"
    for p_id, subject, status in projects:
        emoji = "⏳" if status == "Pending" else "✅" if status == "Accepted" else "❌"
        response += f"#{p_id} | {subject} - {emoji} {status}\n"
    await message.answer(response)