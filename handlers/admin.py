"""
Admin Handler Module
Manages the admin control panel, broadcasting, and project management logic.
"""

import asyncio
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import ADMIN_ID
from states import AdminStates
from database import (
    get_pending_projects, 
    update_project_status, 
    execute_query
)

router = Router()

# --- ADMIN DASHBOARD ---

@router.message(Command("admin"), F.from_user.id == ADMIN_ID)
async def admin_dashboard(message: types.Message):
    """Displays the main admin control panel with navigation buttons."""
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📊 Pending Projects", callback_data="view_pending"))
    builder.row(types.InlineKeyboardButton(text="📢 Broadcast Message", callback_data="admin_broadcast"))
    
    await message.answer("🛠 **Admin Control Panel**", reply_markup=builder.as_markup())

# --- BROADCAST SYSTEM ---

@router.callback_query(F.data == "admin_broadcast", F.from_user.id == ADMIN_ID)
async def trigger_broadcast(callback: types.CallbackQuery, state: FSMContext):
    """Initiates the broadcast state machine."""
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_broadcast"))
    
    await callback.message.answer("📢 Enter the message you want to send to ALL users:", reply_markup=builder.as_markup())
    await state.set_state(AdminStates.waiting_for_broadcast)
    await callback.answer()

@router.message(AdminStates.waiting_for_broadcast, F.from_user.id == ADMIN_ID)
async def execute_broadcast(message: types.Message, state: FSMContext, bot):
    """Sends a message to every user who has ever submitted a project."""
    # Get unique users from the database
    users = execute_query("SELECT DISTINCT user_id FROM projects", fetch=True)
    
    count = 0
    for (u_id,) in users:
        try:
            await bot.send_message(u_id, f"🔔 **ANNOUNCEMENT:**\n\n{message.text}")
            count += 1
            await asyncio.sleep(0.05)  # Flood prevention
        except Exception:
            continue

    await message.answer(f"✅ Broadcast complete. Sent to {count} users.")
    await state.clear()

@router.callback_query(F.data == "cancel_broadcast", F.from_user.id == ADMIN_ID)
async def cancel_broadcast_btn(callback: types.CallbackQuery, state: FSMContext):
    """Resets the state if the admin cancels the broadcast."""
    await state.clear()
    await callback.message.edit_text("🚫 Broadcast cancelled.")
    await callback.answer()

# --- PROJECT MANAGEMENT ---
@router.callback_query(F.data == "view_pending", F.from_user.id == ADMIN_ID)
async def admin_view_pending(callback: types.CallbackQuery):
    """Lists all pending projects as clickable buttons."""
    pending = get_pending_projects()

    if not pending:
        await callback.answer("No pending projects! ✅", show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    
    # Create a button for each project
    for p_id, subject, u_id in pending:
        builder.row(types.InlineKeyboardButton(
            text=f"📂 #{p_id}: {subject}", 
            callback_data=f"manage_{p_id}"
        ))
    
    # Add a back button to return to main admin panel
    builder.row(types.InlineKeyboardButton(text="⬅️ Back", callback_data="back_to_admin"))

    await callback.message.edit_text(
        "📂 **Select a project to manage:**", 
        reply_markup=builder.as_markup()
    )
    await callback.answer()
@router.callback_query(F.data == "back_to_admin", F.from_user.id == ADMIN_ID)
async def back_to_admin(callback: types.CallbackQuery):
    """Returns to the main admin dashboard."""
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📊 Pending Projects", callback_data="view_pending"))
    builder.row(types.InlineKeyboardButton(text="📢 Broadcast Message", callback_data="admin_broadcast"))
    
    await callback.message.edit_text("🛠 **Admin Control Panel**", reply_markup=builder.as_markup())
    await callback.answer()

# --- STUDENT INTERACTION (ACCEPT/DENY) ---

@router.callback_query(F.data.startswith("accept_"))
async def handle_accept(callback: types.CallbackQuery, bot):
    """Handles student confirmation when they accept an admin's offer."""
    proj_id = callback.data.split("_")[1]
    update_project_status(proj_id, "Accepted")
    
    await callback.message.edit_text("✅ **Offer Accepted!**\nThe tutor has been notified and is starting work.")
    await bot.send_message(ADMIN_ID, f"🚀 **SUCCESS:** Project #{proj_id} was accepted by the student.")
    await callback.answer()

@router.callback_query(F.data.startswith("deny_"))
async def handle_deny(callback: types.CallbackQuery):
    """Handles student rejection of an offer."""
    proj_id = callback.data.split("_")[1]
    update_project_status(proj_id, "Denied")
    
    await callback.message.edit_text("❌ **Offer Declined.**\nThe request has been closed.")
    await callback.answer()
@router.callback_query(F.data.startswith("manage_"), F.from_user.id == ADMIN_ID)
async def view_project_details(callback: types.CallbackQuery):
    """Shows full details of a specific project with management options."""
    proj_id = callback.data.split("_")[1]
    
    # Fetch all details for this specific project
    project = execute_query(
        "SELECT id, subject_name, tutor_name, deadline, details, file_id FROM projects WHERE id = ?", 
        (proj_id,), 
        fetch_one=True
    )
    
    if not project:
        await callback.answer("Project not found! ❌")
        return

    p_id, sub, tutor, dead, details, file_id = project

    text = (
        f"📑 **Project Details: #{p_id}**\n\n"
        f"📚 **Subject:** {sub}\n"
        f"👨‍🏫 **Tutor:** {tutor}\n"
        f"📅 **Deadline:** {dead}\n"
        f"📝 **Details:** {details}\n"
    )

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="💰 Send Offer", callback_data=f"make_offer_{p_id}"))
    builder.row(types.InlineKeyboardButton(text="❌ Reject", callback_data=f"deny_{p_id}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Back to List", callback_data="view_pending"))

    # If there's a file, we send it; otherwise, we just edit the text
    if file_id:
        await callback.message.answer_document(file_id, caption=text, reply_markup=builder.as_markup())
        await callback.message.delete() # Remove the menu to keep chat clean
    else:
        await callback.message.edit_text(text, reply_markup=builder.as_markup())
    
    await callback.answer()