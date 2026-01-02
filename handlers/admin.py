from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
import sqlite3
import asyncio
from config import ADMIN_ID
from states import AdminStates

from database import get_pending_projects, update_project_status # Add update_project_status here
router = Router()

@router.message(Command("admin"), F.from_user.id == ADMIN_ID)
async def admin_dashboard(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📊 Pending Projects", callback_data="view_pending"))
    builder.row(types.InlineKeyboardButton(text="📢 Broadcast Message", callback_data="admin_broadcast"))
    
    await message.answer("🛠 **Admin Control Panel**", reply_markup=builder.as_markup())

@router.callback_query(F.data == "admin_broadcast", F.from_user.id == ADMIN_ID)
async def trigger_broadcast(callback: types.CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_broadcast"))
    
    await callback.message.answer("📢 Enter broadcast message:", reply_markup=builder.as_markup())
    await state.set_state(AdminStates.waiting_for_broadcast)
    await callback.answer()

@router.message(AdminStates.waiting_for_broadcast, F.from_user.id == ADMIN_ID)
async def execute_broadcast(message: types.Message, state: FSMContext, bot):
    conn = sqlite3.connect("bot_requests.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT user_id FROM projects")
    users = cursor.fetchall()
    conn.close()

    count = 0
    for (u_id,) in users:
        try:
            await bot.send_message(u_id, f"🔔 **ANNOUNCEMENT:**\n\n{message.text}")
            count += 1
            await asyncio.sleep(0.05)
        except: pass

    await message.answer(f"✅ Sent to {count} users.")
    await state.clear()

@router.callback_query(F.data == "cancel_broadcast", F.from_user.id == ADMIN_ID)
async def cancel_broadcast_btn(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("🚫 Broadcast cancelled.")
    await callback.answer()
from database import get_pending_projects  # Import the helper

@router.callback_query(F.data == "view_pending", F.from_user.id == ADMIN_ID)
async def admin_view_pending(callback: types.CallbackQuery):
    pending = get_pending_projects()  # Just call the function

    if not pending:
        await callback.answer("No pending projects! ✅", show_alert=True)
        return

    text = "⏳ **Pending Projects:**\n\n"
    for p_id, subject, u_id in pending:
        text += f"ID: #{p_id} | {subject} (User: {u_id})\n"
    
    await callback.message.answer(text)
    await callback.answer() # This removes the 'loading' clock on the button
@router.callback_query(F.data.startswith("accept_"))
async def handle_accept(callback: types.CallbackQuery, bot):
    """Triggered when a student clicks 'Accept' on an offer."""
    proj_id = callback.data.split("_")[1]
    
    # Update status in DB
    update_project_status(proj_id, "Accepted")
    
    # Update the message for the user
    await callback.message.edit_text("✅ Offer Accepted! The tutor is starting work.")
    
    # Notify the Admin
    await bot.send_message(ADMIN_ID, f"🚀 Project #{proj_id} was ACCEPTED by the student.")
    await callback.answer()

@router.callback_query(F.data.startswith("deny_"))
async def handle_deny(callback: types.CallbackQuery):
    """Triggered when a student clicks 'Deny' on an offer."""
    proj_id = callback.data.split("_")[1]
    
    # Update status in DB
    update_project_status(proj_id, "Denied")
    
    await callback.message.edit_text("❌ Offer Declined.")
    await callback.answer()