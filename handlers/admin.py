"""
Admin Handler Module - Final Polished Version
"""
import asyncio
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from config import ADMIN_ID
from states import AdminStates
from database import get_pending_projects, update_project_status, execute_query

router = Router()

# --- ADMIN DASHBOARD ---

@router.message(Command("admin"), F.from_user.id == ADMIN_ID)
async def admin_dashboard(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📊 Pending Projects", callback_data="view_pending"))
    builder.row(types.InlineKeyboardButton(text="✅ Accepted/Ongoing", callback_data="view_accepted"))
    builder.row(types.InlineKeyboardButton(text="📜 Project History", callback_data="view_history"))
    builder.row(types.InlineKeyboardButton(text="📢 Broadcast Message", callback_data="admin_broadcast"))
    await message.answer("🛠 **Admin Control Panel**", reply_markup=builder.as_markup())

@router.callback_query(F.data == "back_to_admin", F.from_user.id == ADMIN_ID)
async def back_to_admin(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📊 Pending Projects", callback_data="view_pending"))
    builder.row(types.InlineKeyboardButton(text="✅ Accepted/Ongoing", callback_data="view_accepted"))
    builder.row(types.InlineKeyboardButton(text="📜 Project History", callback_data="view_history"))
    builder.row(types.InlineKeyboardButton(text="📢 Broadcast Message", callback_data="admin_broadcast"))
    await callback.message.edit_text("🛠 **Admin Control Panel**", reply_markup=builder.as_markup())

# --- BROADCAST SYSTEM ---

@router.callback_query(F.data == "admin_broadcast", F.from_user.id == ADMIN_ID)
async def trigger_broadcast(callback: types.CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="❌ Cancel", callback_data="back_to_admin"))
    await callback.message.answer("📢 Enter broadcast message:", reply_markup=builder.as_markup())
    await state.set_state(AdminStates.waiting_for_broadcast)

@router.message(AdminStates.waiting_for_broadcast, F.from_user.id == ADMIN_ID)
async def execute_broadcast(message: types.Message, state: FSMContext, bot):
    users = execute_query("SELECT DISTINCT user_id FROM projects", fetch=True)
    count = 0
    for (u_id,) in users:
        try:
            await bot.send_message(u_id, f"🔔 **ANNOUNCEMENT:**\n\n{message.text}")
            count += 1
            await asyncio.sleep(0.05)
        except: continue
    await message.answer(f"✅ Sent to {count} users.")
    await state.clear()

# --- PROJECT MANAGEMENT (PENDING) ---

@router.callback_query(F.data == "view_pending", F.from_user.id == ADMIN_ID)
async def admin_view_pending(callback: types.CallbackQuery):
    pending = get_pending_projects()
    builder = InlineKeyboardBuilder()
    if not pending:
        builder.row(types.InlineKeyboardButton(text="⬅️ Back", callback_data="back_to_admin"))
        await callback.message.edit_text("No pending projects! ✅", reply_markup=builder.as_markup())
        return

    for p_id, subject, u_id in pending:
        builder.row(types.InlineKeyboardButton(text=f"📂 #{p_id}: {subject}", callback_data=f"manage_{p_id}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Back", callback_data="back_to_admin"))
    await callback.message.edit_text("📂 **Select a project:**", reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith("manage_"), ~(F.data.contains("accepted")), F.from_user.id == ADMIN_ID)
async def view_project_details(callback: types.CallbackQuery):
    proj_id = callback.data.split("_")[1]
    project = execute_query("SELECT id, subject_name, tutor_name, deadline, details, file_id FROM projects WHERE id = ?", (proj_id,), fetch_one=True)
    
    if not project: return
    p_id, sub, tutor, dead, details, file_id = project
    text = f"📑 **Pending Project #{p_id}**\n\n**Sub:** {sub}\n**Tutor:** {tutor}\n**Date:** {dead}\n**Notes:** {details}"
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="💰 Send Offer", callback_data=f"make_offer_{p_id}"))
    builder.row(types.InlineKeyboardButton(text="❌ Reject", callback_data=f"deny_{p_id}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Back", callback_data="view_pending"))
    
    if file_id:
        await callback.message.answer_document(file_id, caption=text, reply_markup=builder.as_markup())
        await callback.message.delete()
    else:
        await callback.message.edit_text(text, reply_markup=builder.as_markup())
# --- OFFER FLOW ---

@router.callback_query(F.data.startswith("make_offer_"), F.from_user.id == ADMIN_ID)
async def start_offer_flow(callback: types.CallbackQuery, state: FSMContext):
    proj_id = callback.data.split("_")[2]
    await state.update_data(offer_proj_id=proj_id)
    await callback.message.answer(f"💰 **Project #{proj_id}**\nWhat is the **Price**?")
    await state.set_state(AdminStates.waiting_for_price)

@router.message(AdminStates.waiting_for_price, F.from_user.id == ADMIN_ID)
async def process_price(message: types.Message, state: FSMContext):
    await state.update_data(price=message.text)
    await message.answer("📅 What is the **Delivery Date**?")
    await state.set_state(AdminStates.waiting_for_delivery)

@router.message(AdminStates.waiting_for_delivery, F.from_user.id == ADMIN_ID)
async def process_delivery(message: types.Message, state: FSMContext):
    await state.update_data(delivery=message.text)
    builder = ReplyKeyboardBuilder()
    builder.button(text="Yes")
    builder.button(text="No, send now")
    await message.answer("📝 Add additional notes?", reply_markup=builder.as_markup(resize_keyboard=True))
    await state.set_state(AdminStates.waiting_for_notes_decision)

@router.message(AdminStates.waiting_for_notes_decision, F.from_user.id == ADMIN_ID)
async def process_notes_decision(message: types.Message, state: FSMContext, bot):
    if message.text.lower() == "yes":
        await message.answer("🖋 Type your notes:", reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(AdminStates.waiting_for_notes_text)
    else:
        await finalize_and_send_offer(message, state, bot, notes_text="None")

@router.message(AdminStates.waiting_for_notes_text, F.from_user.id == ADMIN_ID)
async def process_notes_text(message: types.Message, state: FSMContext, bot):
    await finalize_and_send_offer(message, state, bot, notes_text=message.text)

async def finalize_and_send_offer(message: types.Message, state: FSMContext, bot, notes_text: str):
    data = await state.get_data()
    proj_id = data['offer_proj_id']
    result = execute_query("SELECT user_id, subject_name FROM projects WHERE id = ?", (proj_id,), fetch_one=True)
    if result:
        user_id, subject = result
        offer_text = (f"🎁 **New Offer for {subject}!**\n━━━━━━━━━━━━━\n"
                      f"💰 **Price:** {data['price']}\n📅 **Delivery:** {data['delivery']}\n"
                      f"📝 **Notes:** {notes_text}\n━━━━━━━━━━━━━")
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="✅ Accept", callback_data=f"accept_{proj_id}"))
        builder.row(types.InlineKeyboardButton(text="❌ Deny", callback_data=f"deny_{proj_id}"))
        await bot.send_message(user_id, offer_text, reply_markup=builder.as_markup())
        await message.answer(f"✅ Offer sent!", reply_markup=types.ReplyKeyboardRemove())
    await state.clear()

# --- ONGOING & FINISHING WORK ---

@router.callback_query(F.data == "view_accepted", F.from_user.id == ADMIN_ID)
async def admin_view_accepted(callback: types.CallbackQuery):
    accepted = execute_query("SELECT id, subject_name FROM projects WHERE status = 'Accepted'", fetch=True)
    builder = InlineKeyboardBuilder()
    if not accepted:
        builder.row(types.InlineKeyboardButton(text="⬅️ Back", callback_data="back_to_admin"))
        await callback.message.edit_text("No ongoing projects. 🏖", reply_markup=builder.as_markup())
        return
    for p_id, subject in accepted:
        builder.row(types.InlineKeyboardButton(text=f"🚀 #{p_id}: {subject}", callback_data=f"manage_accepted_{p_id}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Back", callback_data="back_to_admin"))
    await callback.message.edit_text("🚀 **Ongoing Projects:**", reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith("manage_accepted_"), F.from_user.id == ADMIN_ID)
async def manage_accepted_project(callback: types.CallbackQuery, state: FSMContext):
    # Extract ID correctly: manage_accepted_123 -> split by _ is ['manage', 'accepted', '123']
    parts = callback.data.split("_")
    proj_id = parts[2] 
    
    await state.update_data(finish_proj_id=proj_id)
    await state.set_state(AdminStates.waiting_for_finished_work)
    
    await callback.message.answer(
        f"📤 **Project #{proj_id}**\n\n"
        "Please **upload the final file** or type the final message for the student."
    )
    await callback.answer()

@router.message(AdminStates.waiting_for_finished_work, F.from_user.id == ADMIN_ID)
async def process_finished_work(message: types.Message, state: FSMContext, bot):
    data = await state.get_data()
    proj_id = data.get('finish_proj_id')
    result = execute_query("SELECT user_id, subject_name FROM projects WHERE id = ?", (proj_id,), fetch_one=True)
    if result:
        user_id, subject = result
        await bot.send_message(user_id, f"🎉 **WORK COMPLETED!**\nProject: {subject} (#{proj_id})")
        if message.document: await bot.send_document(user_id, message.document.file_id, caption=message.caption)
        elif message.photo: await bot.send_photo(user_id, message.photo[-1].file_id, caption=message.caption)
        else: await bot.send_message(user_id, message.text)
        update_project_status(proj_id, "Finished")
        await message.answer(f"✅ Project #{proj_id} Finished!")
    await state.clear()

# --- HISTORY ---

@router.callback_query(F.data == "view_history", F.from_user.id == ADMIN_ID)
async def admin_view_history(callback: types.CallbackQuery):
    history = execute_query("SELECT id, subject_name, status FROM projects WHERE status IN ('Denied', 'Finished')", fetch=True)
    builder = InlineKeyboardBuilder()
    if not history:
        builder.row(types.InlineKeyboardButton(text="⬅️ Back", callback_data="back_to_admin"))
        await callback.message.edit_text("History is empty. 📭", reply_markup=builder.as_markup())
        return
    text = "📜 **Project History:**\n\n"
    for p_id, subject, status in history:
        icon = "❌" if status == "Denied" else "🏁"
        text += f"{icon} #{p_id} | {subject} ({status})\n"
    builder.row(types.InlineKeyboardButton(text="⬅️ Back", callback_data="back_to_admin"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup())

# --- STUDENT CALLBACKS (NO ADMIN FILTER) ---

@router.callback_query(F.data.startswith("accept_"))
async def handle_accept(callback: types.CallbackQuery, bot):
    proj_id = callback.data.split("_")[1]
    update_project_status(proj_id, "Accepted")
    await callback.message.edit_text("✅ **Offer Accepted!**")
    await bot.send_message(ADMIN_ID, f"🚀 Project #{proj_id} ACCEPTED!")

@router.callback_query(F.data.startswith("deny_"))
async def handle_deny(callback: types.CallbackQuery, bot):
    proj_id = callback.data.split("_")[1]
    update_project_status(proj_id, "Denied")
    if str(callback.from_user.id) == str(ADMIN_ID):
        res = execute_query("SELECT user_id FROM projects WHERE id = ?", (proj_id,), fetch_one=True)
        if res: await bot.send_message(res[0], f"❌ Project #{proj_id} declined by admin.")
        await callback.message.edit_text("🚫 Project rejected.")
    else:
        await bot.send_message(ADMIN_ID, f"❌ Student declined Project #{proj_id}.")
        await callback.message.edit_text("❌ You declined the offer.")
    await callback.answer()