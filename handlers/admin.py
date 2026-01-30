"""
Admin Handler Module
====================
Manages the administrative interface, including project oversight,
offer generation, payment verification, and global broadcasting.
"""

import asyncio
import logging

from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from config import ADMIN_ID
from database import (
    STATUS_ACCEPTED,
    STATUS_REJECTED_PAYMENT,
    get_accepted_projects,
    get_all_payments,
    get_all_projects_categorized,
    get_all_users,
    get_history_projects,
    get_payment_by_id,
    get_pending_projects,
    get_project_by_id,
    update_offer_details,
    update_payment_status,
    update_project_status,
)
from keyboards.admin_kb import (
    get_accepted_projects_kb,
    get_admin_dashboard_kb,
    get_back_btn,
    get_cancel_kb,
    get_manage_project_kb,
    get_notes_decision_kb,
    get_payment_history_kb,
    get_pending_projects_kb,
)
from keyboards.client_kb import get_offer_actions_kb
from states import AdminStates
from utils.constants import (
    BTN_CANCEL,
    BTN_YES,
    MSG_ADMIN_DASHBOARD,
    MSG_ASK_DELIVERY,
    MSG_ASK_NOTES,
    MSG_ASK_NOTES_TEXT,
    MSG_ASK_PRICE,
    MSG_BROADCAST_PROMPT,
    MSG_BROADCAST_SUCCESS,
    MSG_CANCELLED,
    MSG_FINISHED_CONFIRM,
    MSG_NO_NOTES,
    MSG_OFFER_SENT,
    MSG_PAYMENT_CONFIRMED_ADMIN,
    MSG_PAYMENT_CONFIRMED_CLIENT,
    MSG_PAYMENT_REJECTED_ADMIN,
    MSG_PAYMENT_REJECTED_CLIENT,
    MSG_PROJECT_CLOSED,
    MSG_PROJECT_DENIED_CLIENT,
    MSG_PROJECT_DENIED_STUDENT_TO_ADMIN,
    MSG_PROJECT_DETAILS_HEADER,
    MSG_UPLOAD_FINISHED_WORK,
    MSG_WORK_FINISHED_ALERT,
    STATUS_ACCEPTED,
    STATUS_DENIED_ADMIN,
    STATUS_DENIED_STUDENT,
    STATUS_FINISHED,
    STATUS_OFFERED,
    STATUS_REJECTED_PAYMENT,
)
from utils.formatters import (
    escape_md,
    format_master_report,
    format_payment_list,
    format_project_history,
    format_project_list,
)
from utils.helpers import get_file_id

# Initialize router for admin-only events
router = Router()
logger = logging.getLogger(__name__)

# --- NAVIGATION HANDLERS ---


@router.message(F.text == BTN_CANCEL, F.from_user.id == ADMIN_ID)
async def admin_cancel_process(message: types.Message, state: FSMContext):
    """Cancels any active admin FSM state."""
    current_state = await state.get_state()
    if current_state:
        await state.clear()
        await message.answer(MSG_CANCELLED, reply_markup=types.ReplyKeyboardRemove())
        await admin_dashboard(message)  # Return to dashboard
    else:
        await admin_dashboard(message)


@router.message(Command("admin"), F.from_user.id == ADMIN_ID)
async def admin_dashboard(message: types.Message):
    """Entry point: Displays the administrative control panel."""
    await message.answer(MSG_ADMIN_DASHBOARD, reply_markup=get_admin_dashboard_kb())


@router.callback_query(F.data == "back_to_admin", F.from_user.id == ADMIN_ID)
async def back_to_admin(callback: types.CallbackQuery):
    """Returns the user to the main dashboard menu."""
    await callback.message.edit_text(
        MSG_ADMIN_DASHBOARD,
        parse_mode="Markdown",
        reply_markup=get_admin_dashboard_kb(),
    )


# --- DATA VIEW HANDLERS ---


@router.callback_query(F.data == "view_all_master", F.from_user.id == ADMIN_ID)
async def view_all_master(callback: types.CallbackQuery):
    """Fetches and displays a categorized report of every project in the database."""
    projects = await get_all_projects_categorized()
    await callback.message.edit_text(
        format_master_report(projects),
        parse_mode="Markdown",
        reply_markup=get_back_btn().as_markup(),
    )


@router.callback_query(F.data == "view_pending", F.from_user.id == ADMIN_ID)
async def admin_view_pending(callback: types.CallbackQuery):
    """Lists all projects awaiting admin review with management deep-links."""
    pending = await get_pending_projects()
    text = format_project_list(pending, "📊 مشاريع قيد الانتظار")

    # Use reusable keyboard function
    markup = get_pending_projects_kb(pending)

    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=markup)


@router.callback_query(F.data == "view_accepted", F.from_user.id == ADMIN_ID)
async def admin_view_accepted(callback: types.CallbackQuery):
    """Lists active/ongoing projects that are ready for final submission."""
    accepted = await get_accepted_projects()
    text = format_project_list(accepted, "🚀 مشاريع جارية")

    markup = get_accepted_projects_kb(accepted)

    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=markup)


@router.callback_query(F.data == "view_history", F.from_user.id == ADMIN_ID)
async def admin_view_history(callback: types.CallbackQuery):
    """Displays a read-only log of finished or denied projects."""
    history = await get_history_projects()
    await callback.message.edit_text(
        format_project_history(history),
        parse_mode="Markdown",
        reply_markup=get_back_btn().as_markup(),
    )


@router.callback_query(F.data == "view_payments", F.from_user.id == ADMIN_ID)
async def admin_view_payments(callback: types.CallbackQuery):
    """Displays a log of all payments (Pending, Accepted, Rejected)."""
    payments = await get_all_payments()
    await callback.message.edit_text(
        format_payment_list(payments),
        parse_mode="Markdown",
        reply_markup=get_payment_history_kb(payments),
    )


@router.callback_query(F.data.startswith("view_receipt_"), F.from_user.id == ADMIN_ID)
async def admin_view_receipt(callback: types.CallbackQuery, bot):
    """Fetches and sends the actual receipt file for a specific payment."""
    payment_id = callback.data.split("_")[2]
    payment = await get_payment_by_id(payment_id)

    if not payment:
        await callback.answer("⚠️ File not found.", show_alert=True)
        return

    file_id = payment["file_id"]
    status = payment["status"]
    caption = f"📄 **Detail View: Payment #{payment_id}**\nStatus: {status}"

    try:
        # We don't know if it's a photo or document, so we try sending as document (safe bet)
        # or we could rely on how aiogram handles file_ids.
        # Generally send_document works for both if we treat it as a file.
        # But let's try send_photo if it looks like one, or default to document.
        # Simple approach: Just send_document as it's the most versatile.
        await bot.send_document(
            ADMIN_ID, file_id, caption=caption, parse_mode="Markdown"
        )
        await callback.answer()
    except Exception:
        # Fallback if it's a photo ID that send_document doesn't like
        await bot.send_photo(ADMIN_ID, file_id, caption=caption, parse_mode="Markdown")
        await callback.answer()


# --- GLOBAL COMMUNICATION ---


@router.callback_query(F.data == "admin_broadcast", F.from_user.id == ADMIN_ID)
async def trigger_broadcast(callback: types.CallbackQuery, state: FSMContext):
    """Initiates the broadcast FSM flow."""
    await callback.message.answer(MSG_BROADCAST_PROMPT, reply_markup=get_cancel_kb())
    await state.set_state(AdminStates.waiting_for_broadcast)


@router.message(AdminStates.waiting_for_broadcast, F.from_user.id == ADMIN_ID)
async def execute_broadcast(message: types.Message, state: FSMContext, bot):
    """Sends a mass message to all unique users found in the database."""
    users = await get_all_users()
    count = 0
    for u_id in users:
        try:
            await bot.send_message(u_id, f"🔔 **إعلان هام:**\n\n{message.text}")
            count += 1
            await asyncio.sleep(0.05)  # Prevent Telegram flood limit (30 msg/sec)
        except Exception as e:
            logger.warning(f"Failed to broadcast to {u_id}: {e}")
            continue  # Skip users who blocked the bot
    await message.answer(
        MSG_BROADCAST_SUCCESS.format(count), reply_markup=types.ReplyKeyboardRemove()
    )
    await state.clear()


# --- OFFER GENERATION FSM ---


@router.callback_query(
    F.data.startswith("manage_"),
    ~(F.data.contains("accepted")),
    F.from_user.id == ADMIN_ID,
)
async def view_project_details(callback: types.CallbackQuery):
    """Displays detailed project specs and original file for admin review."""
    proj_id = callback.data.split("_")[1]
    project = await get_project_by_id(proj_id)
    if not project:
        return

    p_id = project["id"]
    sub = escape_md(project["subject_name"])
    tutor = escape_md(project["tutor_name"])
    dead = escape_md(project["deadline"])
    details = escape_md(project["details"])
    file_id = project["file_id"]

    # User Info Construction
    u_id = project["user_id"]
    name = escape_md(project["user_full_name"] or "Unknown")
    username = escape_md(project["username"])

    user_line = f"👤 [{name}](tg://user?id={u_id})"
    if username:
        user_line += f" (@{username})"

    text = (
        MSG_PROJECT_DETAILS_HEADER.format(p_id) + "\n"
        f"{user_line}\n"
        f"**المادة:** {sub}\n"
        f"**المدرس:** {tutor}\n"
        f"**الموعد:** {dead}\n"
        f"**التفاصيل:** {details}"
    )

    markup = get_manage_project_kb(p_id)

    # Handle original file display
    if file_id:
        await callback.message.answer_document(
            file_id, caption=text, parse_mode="Markdown", reply_markup=markup
        )
        await callback.message.delete()
    else:
        await callback.message.edit_text(
            text, parse_mode="Markdown", reply_markup=markup
        )


@router.callback_query(F.data.startswith("make_offer_"), F.from_user.id == ADMIN_ID)
async def start_offer_flow(callback: types.CallbackQuery, state: FSMContext):
    """Starts a step-by-step FSM to collect price and delivery data."""
    proj_id = callback.data.split("_")[2]
    await state.update_data(offer_proj_id=proj_id)
    await callback.message.answer(
        MSG_ASK_PRICE.format(proj_id), reply_markup=get_cancel_kb()
    )
    await state.set_state(AdminStates.waiting_for_price)


@router.message(AdminStates.waiting_for_price, F.from_user.id == ADMIN_ID)
async def process_price(message: types.Message, state: FSMContext):
    """Stores price and requests delivery date."""
    price_text = message.text.strip()

    # VALIDATION: Check for reasonable length and empty content
    if not price_text:
        await message.answer("⚠️ الرجاء إدخال سعر صالح.")
        return

    if len(price_text) > 50:
        await message.answer(
            "⚠️ النص طويل جداً. الرجاء إدخال سعر مختصر (مثلاً: 50,000 ل.س)."
        )
        return

    await state.update_data(price=price_text)
    await message.answer(MSG_ASK_DELIVERY, reply_markup=get_cancel_kb())
    await state.set_state(AdminStates.waiting_for_delivery)


@router.message(AdminStates.waiting_for_delivery, F.from_user.id == ADMIN_ID)
async def process_delivery(message: types.Message, state: FSMContext):
    """Stores delivery date and asks if extra notes are needed."""
    delivery_text = message.text.strip()

    # VALIDATION
    if not delivery_text:
        await message.answer("⚠️ الرجاء إدخال موعد صالح.")
        return

    if len(delivery_text) > 50:
        await message.answer("⚠️ النص طويل جداً. حاول الاختصار (مثلاً: 2024-05-01).")
        return

    await state.update_data(delivery=delivery_text)

    await message.answer(MSG_ASK_NOTES, reply_markup=get_notes_decision_kb())
    await state.set_state(AdminStates.waiting_for_notes_decision)


@router.message(AdminStates.waiting_for_notes_decision, F.from_user.id == ADMIN_ID)
async def process_notes_decision(message: types.Message, state: FSMContext, bot):
    """Branches FSM based on whether the admin wants to add custom notes."""
    if message.text == BTN_YES:  # Updated to match Arabic button
        await message.answer(
            MSG_ASK_NOTES_TEXT, reply_markup=types.ReplyKeyboardRemove()
        )
        await state.set_state(AdminStates.waiting_for_notes_text)
    else:
        await finalize_and_send_offer(message, state, bot, notes_text=MSG_NO_NOTES)


@router.message(AdminStates.waiting_for_notes_text, F.from_user.id == ADMIN_ID)
async def process_notes_text(message: types.Message, state: FSMContext, bot):
    """Captures final notes and triggers the student notification."""
    await finalize_and_send_offer(message, state, bot, notes_text=message.text)


async def finalize_and_send_offer(
    message: types.Message, state: FSMContext, bot, notes_text: str
):
    """Compiles all collected data into a structured offer and sends it to the student."""
    data = await state.get_data()
    proj_id = data["offer_proj_id"]
    res = await get_project_by_id(proj_id)

    try:
        if res:
            await update_offer_details(proj_id, data["price"], data["delivery"])
            await update_project_status(proj_id, STATUS_OFFERED)
            user_id = res["user_id"]
            subject = escape_md(res["subject_name"])

            # Escape user-provided inputs
            price = escape_md(data["price"])
            delivery = escape_md(data["delivery"])
            notes = escape_md(notes_text)

            offer_text = (
                f"🎁 **عرض جديد لمشروع: {subject}!**\n━━━━━━━━━━━━━\n"
                f"💰 **السعر:** {price}\n📅 **التسليم:** {delivery}\n"
                f"📝 **ملاحظات:** {notes}\n━━━━━━━━━━━━━"
            )

            markup = get_offer_actions_kb(proj_id)

            await bot.send_message(
                user_id, offer_text, parse_mode="Markdown", reply_markup=markup
            )
            await message.answer(
                MSG_OFFER_SENT, reply_markup=types.ReplyKeyboardRemove()
            )

        await state.clear()
    except Exception as e:
        logger.error(f"Failed to send offer for #{proj_id}: {e}", exc_info=True)
        await message.answer(
            "⚠️ حدث خطأ أثناء إرسال العرض.", reply_markup=types.ReplyKeyboardRemove()
        )
        await state.clear()


# --- WORK LIFECYCLE MANAGEMENT ---


@router.callback_query(
    F.data.startswith("manage_accepted_"), F.from_user.id == ADMIN_ID
)
async def manage_accepted_project(callback: types.CallbackQuery, state: FSMContext):
    """Prepares FSM to receive the final project file from the admin."""
    proj_id = callback.data.split("_")[2]
    await state.update_data(finish_proj_id=proj_id)
    await state.set_state(AdminStates.waiting_for_finished_work)
    await callback.message.answer(
        MSG_UPLOAD_FINISHED_WORK.format(proj_id), reply_markup=get_cancel_kb()
    )
    await callback.answer()


@router.message(AdminStates.waiting_for_finished_work, F.from_user.id == ADMIN_ID)
async def process_finished_work(message: types.Message, state: FSMContext, bot):
    """Transfers the final work from admin to student and marks project as 'Finished'."""
    data = await state.get_data()
    proj_id = data.get("finish_proj_id")
    res = await get_project_by_id(proj_id)

    if res:
        u_id = res["user_id"]
        sub = escape_md(res["subject_name"])

        await bot.send_message(
            u_id, MSG_WORK_FINISHED_ALERT.format(sub, proj_id), parse_mode="Markdown"
        )

        # Relay the actual content (supports document, photo, or plain text)
        file_id, file_type = get_file_id(message)
        if file_type == "document":
            await bot.send_document(u_id, file_id, caption=message.caption)
        elif file_type == "photo":
            await bot.send_photo(u_id, file_id, caption=message.caption)
        else:
            await bot.send_message(u_id, message.text)

        await update_project_status(proj_id, STATUS_FINISHED)
        await message.answer(
            MSG_FINISHED_CONFIRM.format(proj_id),
            reply_markup=types.ReplyKeyboardRemove(),
        )

    await state.clear()


# --- PAYMENT WORKFLOW ---


@router.callback_query(F.data.startswith("confirm_pay_"), F.from_user.id == ADMIN_ID)
async def confirm_payment(callback: types.CallbackQuery, bot):
    """Transitions project from 'Verification' to 'Accepted' (Ongoing)."""
    payment_id = callback.data.split("_")[2]

    # 1. Get Payment Info
    payment = await get_payment_by_id(payment_id)
    if not payment:
        await callback.answer("⚠️ Payment not found!", show_alert=True)
        return

    proj_id = payment["project_id"]

    # 2. Update Payment -> Accepted
    await update_payment_status(payment_id, "accepted")

    # 3. Update Project -> Accepted
    await update_project_status(proj_id, STATUS_ACCEPTED)

    res = await get_project_by_id(proj_id)
    if res:
        subject = escape_md(res["subject_name"])
        await bot.send_message(
            res["user_id"],
            MSG_PAYMENT_CONFIRMED_CLIENT.format(subject),
            parse_mode="Markdown",
        )

    await callback.message.edit_caption(
        caption=MSG_PAYMENT_CONFIRMED_ADMIN.format(proj_id)
        + f"\n(Payment #{payment_id} Accepted)",
        parse_mode="Markdown",
    )


@router.callback_query(F.data.startswith("reject_pay_"), F.from_user.id == ADMIN_ID)
async def reject_payment(callback: types.CallbackQuery, bot):
    """Marks project as payment-failed and notifies the student."""
    payment_id = callback.data.split("_")[2]

    payment = await get_payment_by_id(payment_id)
    if not payment:
        return

    proj_id = payment["project_id"]

    # 1. Update Payment -> Rejected
    await update_payment_status(payment_id, "rejected")

    # 2. Update Project -> Offered (Reset so they can try again)
    # We do NOT kill the project. We let them re-upload.
    await update_project_status(proj_id, STATUS_OFFERED)

    res = await get_project_by_id(proj_id)
    if res:
        # Custom reject message telling them to try again
        await bot.send_message(
            res["user_id"],
            "❌ **تم رفض عملية الدفع.**\nالرجاء التأكد من الإيصال وإعادة المحاولة من قائمة 'عروضي'.",
            parse_mode="Markdown",
        )

    await callback.message.edit_caption(
        caption=MSG_PAYMENT_REJECTED_ADMIN.format(proj_id)
        + f"\n(Payment #{payment_id} Rejected)",
        parse_mode="Markdown",
    )


@router.callback_query(F.data.startswith("deny_"))
async def handle_deny(callback: types.CallbackQuery, bot):
    """General denial handler for both Admin rejection and Student cancellation."""
    proj_id = callback.data.split("_")[1]
    if callback.from_user.id == ADMIN_ID:
        await update_project_status(proj_id, STATUS_DENIED_ADMIN)
        res = await get_project_by_id(proj_id)
        if res:
            await bot.send_message(
                res["user_id"], MSG_PROJECT_DENIED_CLIENT.format(proj_id)
            )
    else:
        await update_project_status(proj_id, STATUS_DENIED_STUDENT)
        await bot.send_message(
            ADMIN_ID, MSG_PROJECT_DENIED_STUDENT_TO_ADMIN.format(proj_id)
        )

    await callback.message.edit_text(MSG_PROJECT_CLOSED.format(proj_id))
