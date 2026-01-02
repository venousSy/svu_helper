from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
import sqlite3
import asyncio
from config import ADMIN_ID
from states import AdminStates

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
@router.callback_query(F.data == "view_pending", F.from_user.id == ADMIN_ID)
async def admin_view_pending(callback: types.CallbackQuery):
    """Fetches and displays all projects with 'Pending' status."""
    # We connect to the DB directly here for now
    conn = sqlite3.connect("bot_requests.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, subject_name, user_id FROM projects WHERE status = 'Pending'")
    pending = cursor.fetchall()
    conn.close()

    if not pending:
        # Use an alert so you don't have to send a new message for 'Empty'
        await callback.answer("No pending projects! ✅", show_alert=True)
        return

    text = "⏳ **Pending Projects:**\n\n"
    for p_id, subject, u_id in pending:
        text += f"ID: #{p_id} | {subject} (User: {u_id})\n"
    
    await callback.message.answer(text)
    await callback.answer() # This removes the 'loading' clock on the button