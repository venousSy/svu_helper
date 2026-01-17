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


from config import ADMIN_ID
from states import AdminStates, ProjectOrder
from database import (
    get_pending_projects, update_project_status, execute_query, 
    get_all_projects_categorized,update_offer_details
)
from utils.formatters import format_project_list, format_project_history, format_master_report
from keyboards.admin_kb import (
    get_admin_dashboard_kb, 
    get_back_btn, 
    get_pending_projects_kb, 
    get_accepted_projects_kb,
    get_manage_project_kb,
    get_notes_decision_kb
)
from utils.constants import (
    STATUS_OFFERED, STATUS_ACCEPTED, STATUS_FINISHED, 
    STATUS_REJECTED_PAYMENT, STATUS_DENIED_ADMIN, STATUS_DENIED_STUDENT
)

# Initialize router for admin-only events
router = Router()

# --- NAVIGATION HANDLERS ---

@router.message(Command("admin"), F.from_user.id == ADMIN_ID)
async def admin_dashboard(message: types.Message):
    """Entry point: Displays the administrative control panel."""
    await message.answer("🛠 **لوحة تحكم المسؤول**", reply_markup=get_admin_dashboard_kb())

@router.callback_query(F.data == "back_to_admin", F.from_user.id == ADMIN_ID)
async def back_to_admin(callback: types.CallbackQuery):
    """Returns the user to the main dashboard menu."""
    await callback.message.edit_text("🛠 **لوحة تحكم المسؤول**", reply_markup=get_admin_dashboard_kb())

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
    text = format_project_list(pending, "📊 مشاريع قيد الانتظار")
    
    # Use reusable keyboard function
    markup = get_pending_projects_kb(pending)
    
    await callback.message.edit_text(text, reply_markup=markup)

@router.callback_query(F.data == "view_accepted", F.from_user.id == ADMIN_ID)
async def admin_view_accepted(callback: types.CallbackQuery):
    """Lists active/ongoing projects that are ready for final submission."""
    accepted = execute_query("SELECT id, subject_name FROM projects WHERE status = ?", (STATUS_ACCEPTED,), fetch=True)
    text = format_project_list(accepted, "🚀 مشاريع جارية")
    
    markup = get_accepted_projects_kb(accepted)
    
    await callback.message.edit_text(text, reply_markup=markup)

@router.callback_query(F.data == "view_history", F.from_user.id == ADMIN_ID)
async def admin_view_history(callback: types.CallbackQuery):
    """Displays a read-only log of finished or denied projects."""
    history = execute_query(
        "SELECT id, subject_name, status FROM projects WHERE status IN (?, ?, ?, ?)", 
        (STATUS_FINISHED, STATUS_DENIED_ADMIN, STATUS_DENIED_STUDENT, STATUS_REJECTED_PAYMENT),
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
    await callback.message.answer("📢 أدخل رسالة الإعلان:", reply_markup=get_back_btn().as_markup())
    await state.set_state(AdminStates.waiting_for_broadcast)

@router.message(AdminStates.waiting_for_broadcast, F.from_user.id == ADMIN_ID)
async def execute_broadcast(message: types.Message, state: FSMContext, bot):
    """Sends a mass message to all unique users found in the database."""
    users = execute_query("SELECT DISTINCT user_id FROM projects", fetch=True)
    count = 0
    for row in users:
        u_id = row['user_id']
        try:
            await bot.send_message(u_id, f"🔔 **إعلان هام:**\n\n{message.text}")
            count += 1
            await asyncio.sleep(0.05) # Prevent Telegram flood limit (30 msg/sec)
        except Exception: 
            continue # Skip users who blocked the bot
    await message.answer(f"✅ تم الإرسال إلى {count} مستخدم.")
    await state.clear()

# --- OFFER GENERATION FSM ---

@router.callback_query(F.data.startswith("manage_"), ~(F.data.contains("accepted")), F.from_user.id == ADMIN_ID)
async def view_project_details(callback: types.CallbackQuery):
    """Displays detailed project specs and original file for admin review."""
    proj_id = callback.data.split("_")[1]
    project = execute_query(
        "SELECT id, subject_name, tutor_name, deadline, details, file_id, user_id, username, user_full_name FROM projects WHERE id = ?", 
        (proj_id,), fetch_one=True
    )
    if not project: return
    
    p_id = project['id']
    sub = project['subject_name']
    tutor = project['tutor_name']
    dead = project['deadline']
    details = project['details']
    file_id = project['file_id']
    
    # User Info Construction
    u_id = project['user_id']
    name = project['user_full_name'] or "Unknown"
    username = project['username']
    
    user_line = f"👤 [{name}](tg://user?id={u_id})"
    if username:
        user_line += f" (@{username})"
    
    text = (f"📑 **المشروع #{p_id}**\n"
            f"━━━━━━━━━━━━━\n"
            f"{user_line}\n"
            f"**المادة:** {sub}\n"
            f"**المدرس:** {tutor}\n"
            f"**الموعد:** {dead}\n"
            f"**التفاصيل:** {details}")
    
    markup = get_manage_project_kb(p_id)
    
    # Handle original file display
    if file_id:
        await callback.message.answer_document(file_id, caption=text, reply_markup=markup)
        await callback.message.delete()
    else:
        await callback.message.edit_text(text, reply_markup=markup)

@router.callback_query(F.data.startswith("make_offer_"), F.from_user.id == ADMIN_ID)
async def start_offer_flow(callback: types.CallbackQuery, state: FSMContext):
    """Starts a step-by-step FSM to collect price and delivery data."""
    proj_id = callback.data.split("_")[2]
    await state.update_data(offer_proj_id=proj_id)
    await callback.message.answer(f"💰 **المشروع #{proj_id}**\nما هو **السعر المقترح**؟")
    await state.set_state(AdminStates.waiting_for_price)

@router.message(AdminStates.waiting_for_price, F.from_user.id == ADMIN_ID)
async def process_price(message: types.Message, state: FSMContext):
    """Stores price and requests delivery date."""
    await state.update_data(price=message.text)
    await message.answer("📅 ما هو **موعد التسليم**؟")
    await state.set_state(AdminStates.waiting_for_delivery)

@router.message(AdminStates.waiting_for_delivery, F.from_user.id == ADMIN_ID)
async def process_delivery(message: types.Message, state: FSMContext):
    """Stores delivery date and asks if extra notes are needed."""
    await state.update_data(delivery=message.text)
    
    await message.answer("📝 هل تود إضافة **ملاحظات**؟", reply_markup=get_notes_decision_kb())
    await state.set_state(AdminStates.waiting_for_notes_decision)

@router.message(AdminStates.waiting_for_notes_decision, F.from_user.id == ADMIN_ID)
async def process_notes_decision(message: types.Message, state: FSMContext, bot):
    """Branches FSM based on whether the admin wants to add custom notes."""
    if message.text == "نعم": # Updated to match Arabic button
        await message.answer("🖋 اكتب ملاحظاتك:", reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(AdminStates.waiting_for_notes_text)
    else:
        await finalize_and_send_offer(message, state, bot, notes_text="لا توجد ملاحظات")

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
        update_offer_details(proj_id, data['price'], data['delivery'])
        update_project_status(proj_id, STATUS_OFFERED)
        user_id = res['user_id']
        subject = res['subject_name']
        offer_text = (f"🎁 **عرض جديد لمشروع: {subject}!**\n━━━━━━━━━━━━━\n"
                      f"💰 **السعر:** {data['price']}\n📅 **التسليم:** {data['delivery']}\n"
                      f"📝 **ملاحظات:** {notes_text}\n━━━━━━━━━━━━━")
        
        # We need client KB here for the student to accept/deny
        from keyboards.client_kb import get_offer_actions_kb
        markup = get_offer_actions_kb(proj_id)
        
        await bot.send_message(user_id, offer_text, reply_markup=markup)
        await message.answer(f"✅ تم إرسال العرض!", reply_markup=types.ReplyKeyboardRemove())
    
    await state.clear()

# --- WORK LIFECYCLE MANAGEMENT ---

@router.callback_query(F.data.startswith("manage_accepted_"), F.from_user.id == ADMIN_ID)
async def manage_accepted_project(callback: types.CallbackQuery, state: FSMContext):
    """Prepares FSM to receive the final project file from the admin."""
    proj_id = callback.data.split("_")[2]
    await state.update_data(finish_proj_id=proj_id)
    await state.set_state(AdminStates.waiting_for_finished_work)
    await callback.message.answer(f"📤 **المشروع #{proj_id}**\nارفع العمل النهائي (ملف/صورة/نص):")
    await callback.answer()

@router.message(AdminStates.waiting_for_finished_work, F.from_user.id == ADMIN_ID)
async def process_finished_work(message: types.Message, state: FSMContext, bot):
    """Transfers the final work from admin to student and marks project as 'Finished'."""
    data = await state.get_data()
    proj_id = data.get('finish_proj_id')
    res = execute_query("SELECT user_id, subject_name FROM projects WHERE id = ?", (proj_id,), fetch_one=True)
    
    if res:
        u_id = res['user_id']
        sub = res['subject_name']
        
        await bot.send_message(u_id, f"🎉 **تم إنجاز العمل!**\nالمشروع: {sub} (#{proj_id})")
        # Relay the actual content (supports document, photo, or plain text)
        if message.document: await bot.send_document(u_id, message.document.file_id, caption=message.caption)
        elif message.photo: await bot.send_photo(u_id, message.photo[-1].file_id, caption=message.caption)
        else: await bot.send_message(u_id, message.text)
        
        update_project_status(proj_id, STATUS_FINISHED)
        await message.answer(f"✅ تم إنهاء المشروع #{proj_id}!")
    
    await state.clear()

# --- PAYMENT WORKFLOW ---

@router.callback_query(F.data.startswith("confirm_pay_"), F.from_user.id == ADMIN_ID)
async def confirm_payment(callback: types.CallbackQuery, bot):
    """Transitions project from 'Verification' to 'Accepted' (Ongoing)."""
    proj_id = callback.data.split("_")[2]
    update_project_status(proj_id, STATUS_ACCEPTED)
    res = execute_query("SELECT user_id, subject_name FROM projects WHERE id = ?", (proj_id,), fetch_one=True)
    if res:
        await bot.send_message(res['user_id'], f"🚀 **تم تأكيد الدفع!**\nبدأ العمل على **{res['subject_name']}**.")
    await callback.message.edit_caption(caption=f"✅ **تم التأكيد** المشروع #{proj_id}")

@router.callback_query(F.data.startswith("reject_pay_"), F.from_user.id == ADMIN_ID)
async def reject_payment(callback: types.CallbackQuery, bot):
    """Marks project as payment-failed and notifies the student."""
    proj_id = callback.data.split("_")[2]
    update_project_status(proj_id, STATUS_REJECTED_PAYMENT)
    res = execute_query("SELECT user_id FROM projects WHERE id = ?", (proj_id,), fetch_one=True)
    if res:
        await bot.send_message(res['user_id'], "❌ **رفض الدفع:** تعذر التحقق من الإيصال.")
    await callback.message.edit_caption(caption=f"❌ **مرفوض** المشروع #{proj_id}")

@router.callback_query(F.data.startswith("deny_"))
async def handle_deny(callback: types.CallbackQuery, bot):
    """General denial handler for both Admin rejection and Student cancellation."""
    proj_id = callback.data.split("_")[1]
    if callback.from_user.id == ADMIN_ID:
        update_project_status(proj_id, STATUS_DENIED_ADMIN)
        res = execute_query("SELECT user_id FROM projects WHERE id = ?", (proj_id,), fetch_one=True)
        if res: await bot.send_message(res['user_id'], f"❌ تم رفض المشروع #{proj_id} من قبل المشرف.")
    else:
        update_project_status(proj_id, STATUS_DENIED_STUDENT)
        await bot.send_message(ADMIN_ID, f"❌ قام الطالب بإلغاء المشروع #{proj_id}.")
    
    await callback.message.edit_text(f"🚫 تم إغلاق المشروع #{proj_id}.")