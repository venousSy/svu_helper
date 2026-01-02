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
    """Lists all projects currently marked as 'Pending'."""
    pending = get_pending_projects()

    if not pending:
        await callback.answer("No pending projects! ✅", show_alert=True)
        return

    text = "⏳ **Pending Projects:**\n\n"
    for p_id, subject, u_id in pending:
        text += f"ID: #{p_id} | {subject} (User ID: {u_id})\n"
    
    await callback.message.answer(text)
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
