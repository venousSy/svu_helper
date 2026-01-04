"""
Admin Handler Module
====================
Manages the administrative interface, including project oversight, 
offer generation, payment verification, and global broadcasting.
"""

import asyncio
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from config import ADMIN_ID
from states import AdminStates, ProjectOrder
from database import (
    get_pending_projects, update_project_status, execute_query, 
    get_all_projects_categorized
)
from utils.formatters import format_project_list, format_project_history, format_master_report

# Initialize router for admin-only events
router = Router()

# --- REUSABLE UI COMPONENTS ---

def get_admin_kb() -> types.InlineKeyboardMarkup:
    """Generates the main administrative dashboard keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📑 Master Project List", callback_data="view_all_master"))
    builder.row(types.InlineKeyboardButton(text="📊 Pending Projects", callback_data="view_pending"))
    builder.row(types.InlineKeyboardButton(text="✅ Accepted/Ongoing", callback_data="view_accepted"))
    builder.row(types.InlineKeyboardButton(text="📜 Project History", callback_data="view_history"))
    builder.row(types.InlineKeyboardButton(text="📢 Broadcast Message", callback_data="admin_broadcast"))
    return builder.as_markup()

def get_back_btn(callback_data: str = "back_to_admin") -> InlineKeyboardBuilder:
    """Returns an InlineKeyboardBuilder seeded with a standard 'Back' button."""
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="⬅️ Back", callback_data=callback_data))
    return builder

# --- NAVIGATION HANDLERS ---

@router.message(Command("admin"), F.from_user.id == ADMIN_ID)
async def admin_dashboard(message: types.Message):
    """Entry point: Displays the administrative control panel."""
    await message.answer("🛠 **Admin Control Panel**", reply_markup=get_admin_kb())

@router.callback_query(F.data == "back_to_admin", F.from_user.id == ADMIN_ID)
async def back_to_admin(callback: types.CallbackQuery):
    """Returns the user to the main dashboard menu."""
    await callback.message.edit_text("🛠 **Admin Control Panel**", reply_markup=get_admin_kb())

# --- DATA VIEW HANDLERS ---

@router.callback_query(F.data == "view_all_master", F.from_user.id == ADMIN_ID)
async def view_all_master(callback: types.CallbackQuery):
    """Fetches and displays a categorized report of every project in the database."""
    projects = get_all_projects_categorized()
    await callback.message.edit_text(
        format_master_report(projects), 
        reply_markup=get_back_btn().as_markup()
    )

@router.callback_query(F.data == "view_pending", F.from_user.id == ADMIN_ID)
async def admin_view_pending(callback: types.CallbackQuery):
    """Lists all projects awaiting admin review with management deep-links."""
    pending = get_pending_projects()
    text = format_project_list(pending, "📊 Pending Projects")
    builder = get_back_btn()
    # Dynamically add management buttons for each project
    for p_id, subject, _ in pending:
        builder.row(types.InlineKeyboardButton(text=f"📂 Manage #{p_id}", callback_data=f"manage_{p_id}"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup())

@router.callback_query(F.data == "view_accepted", F.from_user.id == ADMIN_ID)
async def admin_view_accepted(callback: types.CallbackQuery):
    """Lists active/ongoing projects that are ready for final submission."""
    accepted = execute_query("SELECT id, subject_name FROM projects WHERE status = 'Accepted'", fetch=True)
    text = format_project_list(accepted, "🚀 Ongoing Projects")
    builder = get_back_btn()
    for p_id, _ in accepted:
        builder.row(types.InlineKeyboardButton(text=f"📤 Finish #{p_id}", callback_data=f"manage_accepted_{p_id}"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup())

@router.callback_query(F.data == "view_history", F.from_user.id == ADMIN_ID)
async def admin_view_history(callback: types.CallbackQuery):
    """Displays a read-only log of finished or denied projects."""
    history = execute_query(
        "SELECT id, subject_name, status FROM projects WHERE status IN "
        "('Denied', 'Finished', 'Denied: Admin Rejected', 'Denied: Student Cancelled')", 
        fetch=True
    )
    await callback.message.edit_text(
        format_project_history(history), 
        reply_markup=get_back_btn().as_markup()
    )

# --- GLOBAL COMMUNICATION ---

@router.callback_query(F.data == "admin_broadcast", F.from_user.id == ADMIN_ID)
async def trigger_broadcast(callback: types.CallbackQuery, state: FSMContext):
    """Initiates the broadcast FSM flow."""
    await callback.message.answer("📢 Enter broadcast message:", reply_markup=get_back_btn().as_markup())
    await state.set_state(AdminStates.waiting_for_broadcast)

@router.message(AdminStates.waiting_for_broadcast, F.from_user.id == ADMIN_ID)
async def execute_broadcast(message: types.Message, state: FSMContext, bot):
    """Sends a mass message to all unique users found in the database."""
    users = execute_query("SELECT DISTINCT user_id FROM projects", fetch=True)
    count = 0
    for (u_id,) in users:
        try:
            await bot.send_message(u_id, f"🔔 **ANNOUNCEMENT:**\n\n{message.text}")
            count += 1
            await asyncio.sleep(0.05) # Prevent Telegram flood limit (30 msg/sec)
        except Exception: 
            continue # Skip users who blocked the bot
    await message.answer(f"✅ Sent to {count} users.")
    await state.clear()

# --- OFFER GENERATION FSM ---

@router.callback_query(F.data.startswith("manage_"), ~(F.data.contains("accepted")), F.from_user.id == ADMIN_ID)
async def view_project_details(callback: types.CallbackQuery):
    """Displays detailed project specs and original file for admin review."""
    proj_id = callback.data.split("_")[1]
    project = execute_query(
        "SELECT id, subject_name, tutor_name, deadline, details, file_id FROM projects WHERE id = ?", 
        (proj_id,), fetch_one=True
    )
    if not project: return
    
    p_id, sub, tutor, dead, details, file_id = project
    text = f"📑 **Project #{p_id}**\n\n**Sub:** {sub}\n**Tutor:** {tutor}\n**Date:** {dead}\n**Notes:** {details}"
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="💰 Send Offer", callback_data=f"make_offer_{p_id}"))
    builder.row(types.InlineKeyboardButton(text="❌ Reject", callback_data=f"deny_{p_id}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Back", callback_data="view_pending"))
    
    # Handle original file display
    if file_id:
        await callback.message.answer_document(file_id, caption=text, reply_markup=builder.as_markup())
        await callback.message.delete()
    else:
        await callback.message.edit_text(text, reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith("make_offer_"), F.from_user.id == ADMIN_ID)
async def start_offer_flow(callback: types.CallbackQuery, state: FSMContext):
    """Starts a step-by-step FSM to collect price and delivery data."""
    proj_id = callback.data.split("_")[2]
    await state.update_data(offer_proj_id=proj_id)
    await callback.message.answer(f"💰 **Project #{proj_id}**\nWhat is the **Price**?")
    await state.set_state(AdminStates.waiting_for_price)

@router.message(AdminStates.waiting_for_price, F.from_user.id == ADMIN_ID)
async def process_price(message: types.Message, state: FSMContext):
    """Stores price and requests delivery date."""
    await state.update_data(price=message.text)
    await message.answer("📅 What is the **Delivery Date**?")
    await state.set_state(AdminStates.waiting_for_delivery)

@router.message(AdminStates.waiting_for_delivery, F.from_user.id == ADMIN_ID)
async def process_delivery(message: types.Message, state: FSMContext):
    """Stores delivery date and asks if extra notes are needed."""
    await state.update_data(delivery=message.text)
    builder = ReplyKeyboardBuilder()
    builder.button(text="Yes")
    builder.button(text="No, send now")
    await message.answer("📝 Add additional notes?", reply_markup=builder.as_markup(resize_keyboard=True))
    await state.set_state(AdminStates.waiting_for_notes_decision)

@router.message(AdminStates.waiting_for_notes_decision, F.from_user.id == ADMIN_ID)
async def process_notes_decision(message: types.Message, state: FSMContext, bot):
    """Branches FSM based on whether the admin wants to add custom notes."""
    if message.text.lower() == "yes":
        await message.answer("🖋 Type your notes:", reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(AdminStates.waiting_for_notes_text)
    else:
        await finalize_and_send_offer(message, state, bot, notes_text="None")

@router.message(AdminStates.waiting_for_notes_text, F.from_user.id == ADMIN_ID)
async def process_notes_text(message: types.Message, state: FSMContext, bot):
    """Captures final notes and triggers the student notification."""
    await finalize_and_send_offer(message, state, bot, notes_text=message.text)

async def finalize_and_send_offer(message: types.Message, state: FSMContext, bot, notes_text: str):
    """Compiles all collected data into a structured offer and sends it to the student."""
    data = await state.get_data()
    proj_id = data['offer_proj_id']
    res = execute_query("SELECT user_id, subject_name FROM projects WHERE id = ?", (proj_id,), fetch_one=True)
    
    if res:
        user_id, subject = res
        offer_text = (f"🎁 **New Offer for {subject}!**\n━━━━━━━━━━━━━\n"
                      f"💰 **Price:** {data['price']}\n📅 **Delivery:** {data['delivery']}\n"
                      f"📝 **Notes:** {notes_text}\n━━━━━━━━━━━━━")
        
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="✅ Accept", callback_data=f"accept_{proj_id}"))
        builder.row(types.InlineKeyboardButton(text="❌ Deny", callback_data=f"deny_{proj_id}"))
        
        await bot.send_message(user_id, offer_text, reply_markup=builder.as_markup())
        await message.answer(f"✅ Offer sent!", reply_markup=types.ReplyKeyboardRemove())
    
    await state.clear()

# --- WORK LIFECYCLE MANAGEMENT ---

@router.callback_query(F.data.startswith("manage_accepted_"), F.from_user.id == ADMIN_ID)
async def manage_accepted_project(callback: types.CallbackQuery, state: FSMContext):
    """Prepares FSM to receive the final project file from the admin."""
    proj_id = callback.data.split("_")[2]
    await state.update_data(finish_proj_id=proj_id)
    await state.set_state(AdminStates.waiting_for_finished_work)
    await callback.message.answer(f"📤 **Project #{proj_id}**\nUpload final work (File/Photo/Text):")
    await callback.answer()

@router.message(AdminStates.waiting_for_finished_work, F.from_user.id == ADMIN_ID)
async def process_finished_work(message: types.Message, state: FSMContext, bot):
    """Transfers the final work from admin to student and marks project as 'Finished'."""
    data = await state.get_data()
    proj_id = data.get('finish_proj_id')
    res = execute_query("SELECT user_id, subject_name FROM projects WHERE id = ?", (proj_id,), fetch_one=True)
    
    if res:
        u_id, sub = res
        await bot.send_message(u_id, f"🎉 **WORK COMPLETED!**\nProject: {sub} (#{proj_id})")
        # Relay the actual content (supports document, photo, or plain text)
        if message.document: await bot.send_document(u_id, message.document.file_id, caption=message.caption)
        elif message.photo: await bot.send_photo(u_id, message.photo[-1].file_id, caption=message.caption)
        else: await bot.send_message(u_id, message.text)
        
        update_project_status(proj_id, "Finished")
        await message.answer(f"✅ Project #{proj_id} Finished!")
    
    await state.clear()

# --- PAYMENT WORKFLOW ---

@router.callback_query(F.data.startswith("confirm_pay_"), F.from_user.id == ADMIN_ID)
async def confirm_payment(callback: types.CallbackQuery, bot):
    """Transitions project from 'Verification' to 'Accepted' (Ongoing)."""
    proj_id = callback.data.split("_")[2]
    update_project_status(proj_id, "Accepted")
    res = execute_query("SELECT user_id, subject_name FROM projects WHERE id = ?", (proj_id,), fetch_one=True)
    if res:
        await bot.send_message(res[0], f"🚀 **Payment Confirmed!**\nWork started on **{res[1]}**.")
    await callback.message.edit_caption(caption=f"✅ **Confirmed** Project #{proj_id}")

@router.callback_query(F.data.startswith("reject_pay_"), F.from_user.id == ADMIN_ID)
async def reject_payment(callback: types.CallbackQuery, bot):
    """Marks project as payment-failed and notifies the student."""
    proj_id = callback.data.split("_")[2]
    update_project_status(proj_id, "Rejected: Payment Issue")
    res = execute_query("SELECT user_id FROM projects WHERE id = ?", (proj_id,), fetch_one=True)
    if res:
        await bot.send_message(res[0], "❌ **Payment Issue:** Receipt could not be verified.")
    await callback.message.edit_caption(caption=f"❌ **Rejected** Project #{proj_id}")

@router.callback_query(F.data.startswith("deny_"))
async def handle_deny(callback: types.CallbackQuery, bot):
    """General denial handler for both Admin rejection and Student cancellation."""
    proj_id = callback.data.split("_")[1]
    if callback.from_user.id == ADMIN_ID:
        update_project_status(proj_id, "Denied: Admin Rejected")
        res = execute_query("SELECT user_id FROM projects WHERE id = ?", (proj_id,), fetch_one=True)
        if res: await bot.send_message(res[0], f"❌ Project #{proj_id} declined by admin.")
    else:
        update_project_status(proj_id, "Denied: Student Cancelled")
        await bot.send_message(ADMIN_ID, f"❌ Student declined Project #{proj_id}.")
    
    await callback.message.edit_text(f"🚫 Project #{proj_id} closed.")