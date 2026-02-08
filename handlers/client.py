"""
Client Handler Module
=====================
Manages the student-facing Finite State Machine (FSM) for project submissions
and handles status inquiries for existing requests.
"""

from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import ADMIN_IDS
from database import (
    STATUS_AWAITING_VERIFICATION,
    add_payment,
    add_project,
    get_project_by_id,
    get_student_offers,
    get_user_projects,
    update_project_status,
)
from keyboards.admin_kb import get_new_project_alert_kb, get_payment_verify_kb
from keyboards.client_kb import (
    get_cancel_payment_kb,
    get_offer_actions_kb,
    get_offers_list_kb,
)
from states import ProjectOrder
from utils.constants import (
    MSG_ASK_DEADLINE,
    MSG_ASK_DETAILS,
    MSG_ASK_SUBJECT,
    MSG_ASK_TUTOR,
    MSG_NO_DESC,
    MSG_NO_OFFERS,
    MSG_NO_PROJECTS,
    MSG_OFFER_ACCEPTED,
    MSG_OFFER_DETAILS,
    MSG_PROJECT_SUBMITTED,
    MSG_RECEIPT_RECEIVED,
    STATUS_OFFERED,
)
from utils.formatters import (
    escape_md,
    format_admin_notification,
    format_offer_list,
    format_student_projects,
)
from utils.helpers import get_file_id

# Initialize router for student-related events
router = Router()

# --- PROJECT SUBMISSION FLOW (FSM) ---


@router.message(Command("new_project"))
async def start_project(message: types.Message, state: FSMContext):
    """
    Entry point for the project submission wizard.
    Initializes the FSM and requests the subject name.
    """

    await message.answer(MSG_ASK_SUBJECT, parse_mode="Markdown")
    await state.set_state(ProjectOrder.subject)


@router.message(ProjectOrder.subject)
async def process_subject(message: types.Message, state: FSMContext):
    """Stores the subject name and advances to tutor selection."""
    await state.update_data(subject=message.text)
    await message.answer(MSG_ASK_TUTOR, parse_mode="Markdown")
    await state.set_state(ProjectOrder.tutor)


@router.message(ProjectOrder.tutor)
async def process_tutor(message: types.Message, state: FSMContext):
    """Stores the tutor name and advances to deadline input."""
    await state.update_data(tutor=message.text)
    await message.answer(MSG_ASK_DEADLINE, parse_mode="Markdown")
    await state.set_state(ProjectOrder.deadline)


@router.message(ProjectOrder.deadline)
async def process_deadline(message: types.Message, state: FSMContext):
    """Stores the deadline and requests final project documentation/description."""
    await state.update_data(deadline=message.text)
    await message.answer(MSG_ASK_DETAILS, parse_mode="Markdown")
    await state.set_state(ProjectOrder.details)


@router.message(ProjectOrder.details)
async def process_details(message: types.Message, state: FSMContext, bot):
    """
    Finalizes the FSM flow.
    Extracts media or text, saves to DB, and alerts the administrator.
    """
    # Retrieve all data collected during the FSM lifecycle
    data = await state.get_data()

    # Logic: Prioritize document, then photo. Fallback to None if text-only.
    # Logic: Prioritize document, then photo. Fallback to None if text-only.
    file_id, _ = get_file_id(message)

    # Logic: Details can be in the message text or a file caption
    details_text = message.text or message.caption or MSG_NO_DESC

    # Capture user details
    user = message.from_user
    username = user.username  # Can be None
    full_name = user.full_name

    # Commit project to database and retrieve the auto-generated ID
    try:
        project_id = await add_project(
            user_id=user.id,
            username=username,
            user_full_name=full_name,
            subject=data["subject"],
            tutor=data["tutor"],
            deadline=data["deadline"],
            details=details_text,
            file_id=file_id,
        )

        # Provide immediate feedback to the student
        await message.answer(
            MSG_PROJECT_SUBMITTED.format(project_id), parse_mode="Markdown"
        )

        admin_text = format_admin_notification(
            project_id,
            data["subject"],
            data["deadline"],
            details_text,
            user_name=full_name,
            username=username,
        )
        for admin_id in ADMIN_IDS:
            await bot.send_message(
                admin_id,
                admin_text,
                parse_mode="Markdown",
                reply_markup=get_new_project_alert_kb(project_id),
            )

        # Clear FSM state to allow new commands
        await state.clear()

    except Exception as e:
        import logging

        logging.getLogger(__name__).error(
            f"Failed to submit project: {e}", exc_info=True
        )
        await message.answer(
            "⚠️ حدث خطأ أثناء حفظ المشروع. حاول مرة أخرى لاحقاً.",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        await state.clear()


from keyboards.callbacks import MenuCallback, ProjectCallback

# ... (imports)

@router.callback_query(ProjectCallback.filter(F.action == "accept"))
async def student_accept_offer(
    callback: types.CallbackQuery, 
    state: FSMContext, 
    callback_data: ProjectCallback
):
    """Student clicks 'Accept' on the offer."""
    proj_id = callback_data.id

    # Store the project ID in FSM so we know which project the receipt belongs to
    await state.update_data(active_pay_proj_id=proj_id)

    await callback.message.edit_text(
        MSG_OFFER_ACCEPTED.format(proj_id),
        parse_mode="Markdown",
        reply_markup=get_cancel_payment_kb(),  # Add Cancel Button
    )
    # Set the state defined in your states.py
    await state.set_state(ProjectOrder.waiting_for_payment_proof)
    await callback.answer()


@router.callback_query(MenuCallback.filter(F.action == "cancel_pay"))
async def cancel_payment_process(callback: types.CallbackQuery, state: FSMContext):
    """Cancels the payment upload and returns the user to safety."""
    await state.clear()
    await callback.message.edit_text(
        "🚫 تم إلغاء عملية الدفع. يمكنك قبول العرض لاحقاً من قائمة 'عروضي'."
    )
    await callback.answer()

# ... (process_payment_proof, view_projects, view_offers)

@router.callback_query(ProjectCallback.filter(F.action == "view_offer"))
async def show_specific_offer(
    callback: types.CallbackQuery,
    callback_data: ProjectCallback
):
    proj_id = callback_data.id

    # Query the new columns!
    res = await get_project_by_id(proj_id)

    if res:
        subject = escape_md(res["subject_name"])
        price = escape_md(res["price"])
        delivery = escape_md(res["delivery_date"])

        text = MSG_OFFER_DETAILS.format(subject, price, delivery, escape_md(proj_id))

        markup = get_offer_actions_kb(proj_id)

        await callback.message.edit_text(
            text, parse_mode="Markdown", reply_markup=markup
        )
