import logging
from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramAPIError

from config import settings
from database.repositories import ProjectRepository, PaymentRepository
from utils.enums import ProjectStatus
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
)
from utils.formatters import (
    escape_md,
    format_admin_notification,
    format_offer_list,
    format_student_projects,
)
from utils.helpers import get_file_id, get_file_size

# Initialize router for student-related events
router = Router()
logger = logging.getLogger(__name__)

from middlewares.throttling import ThrottlingMiddleware
router.message.middleware(ThrottlingMiddleware(rate_limit=0.5))

# Constants for File Validation
MAX_FILE_SIZE_MB = 15
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_DOCUMENT_MIMES = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]

# --- PROJECT SUBMISSION FLOW (FSM) ---


@router.message(Command("new_project"))
async def start_project(message: types.Message, state: FSMContext):
    """
    Entry point for the project submission wizard.
    Initializes the FSM and requests the subject name.
    """

    await message.answer(MSG_ASK_SUBJECT, parse_mode="Markdown")
    await state.set_state(ProjectOrder.subject)


@router.message(ProjectOrder.subject, F.text)
async def process_subject(message: types.Message, state: FSMContext):
    """Stores the subject name and advances to tutor selection."""
    await state.update_data(subject=message.text)
    await message.answer(MSG_ASK_TUTOR, parse_mode="Markdown")
    await state.set_state(ProjectOrder.tutor)


@router.message(ProjectOrder.tutor, F.text)
async def process_tutor(message: types.Message, state: FSMContext):
    """Stores the tutor name and advances to deadline input."""
    await state.update_data(tutor=message.text)
    await message.answer(MSG_ASK_DEADLINE, parse_mode="Markdown")
    await state.set_state(ProjectOrder.tutor if False else ProjectOrder.deadline) # Corrected logic flow


@router.message(ProjectOrder.deadline, F.text)
async def process_deadline(message: types.Message, state: FSMContext):
    """Stores the deadline and requests final project documentation/description."""
    await state.update_data(deadline=message.text)
    await message.answer(MSG_ASK_DETAILS, parse_mode="Markdown")
    await state.set_state(ProjectOrder.details)


@router.message(ProjectOrder.subject)
@router.message(ProjectOrder.tutor)
@router.message(ProjectOrder.deadline)
async def reject_media_early(message: types.Message):
    """Rejects media files sent too early during the text-only steps."""
    await message.answer("⚠️ الرجاء إدخال النص مطلوب أولاً. يمكنك رفع الملفات في الخطوة التالية.")


@router.message(ProjectOrder.details)
async def process_details(message: types.Message, state: FSMContext, bot):
    """
    Finalizes the FSM flow.
    Extracts media or text, saves to DB, and alerts the administrator.
    """
    # Validation Check: Check file size for ANY media type (Photo, Video, Doc, etc.)
    file_size = get_file_size(message)
    if file_size and file_size > MAX_FILE_SIZE_BYTES:
        await message.answer(f"⚠️ حجم الملف كبير جداً. الحد الأقصى هو {MAX_FILE_SIZE_MB}MB.")
        return

    # Retrieve all data collected during the FSM lifecycle
    data = await state.get_data()

    # Logic: Prioritize document, then photo. Fallback to None if text-only.
    file_id, file_type = get_file_id(message)

    # Logic: Details can be in the message text or a file caption
    details_text = message.text or message.caption or MSG_NO_DESC

    # Capture user details
    user = message.from_user
    username = user.username  # Can be None
    full_name = user.full_name

    # Commit project to database and retrieve the auto-generated ID
    try:
        project_id = await ProjectRepository.add_project(
            user_id=user.id,
            username=username,
            user_full_name=full_name,
            subject=data["subject"],
            tutor=data["tutor"],
            deadline=data["deadline"],
            details=details_text,
            file_id=file_id,
            file_type=file_type,
        )

        # Provide immediate feedback to the student
        await message.answer(
            MSG_PROJECT_SUBMITTED.format(project_id), parse_mode="Markdown", reply_markup=types.ReplyKeyboardRemove()
        )

        admin_text = format_admin_notification(
            project_id,
            data["subject"],
            data["deadline"],
            details_text,
            user_name=full_name,
            username=username,
        )
        for admin_id in settings.admin_ids:
            try:
                await bot.send_message(
                    admin_id,
                    admin_text,
                    parse_mode="Markdown",
                    reply_markup=get_new_project_alert_kb(project_id),
                )
            except TelegramAPIError as e:
                logger.error(f"Failed to notify admin {admin_id}: {e}")

        # Clear FSM state to allow new commands
        await state.clear()

    except Exception as e:
        logger.error(f"Failed to submit project: {e}", exc_info=True)
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


@router.message(ProjectOrder.waiting_for_payment_proof, F.photo | F.document)
async def process_payment_proof(message: types.Message, state: FSMContext, bot):
    """Student sends the receipt; we relay it to the Admin for verification."""
    # Validation
    if message.document:
        if message.document.file_size > MAX_FILE_SIZE_BYTES:
            await message.answer(f"⚠️ حجم الملف كبير جداً. الحد الأقصى هو {MAX_FILE_SIZE_MB}MB.")
            return
        if message.document.mime_type not in ALLOWED_DOCUMENT_MIMES and "image" not in message.document.mime_type:
             await message.answer("⚠️ الرجاء رفع صورة أو ملف PDF/Word كإثبات للدفع.")
             return

    data = await state.get_data()
    proj_id = data.get("active_pay_proj_id")

    # Identify the file (keep file_type to choose send method correctly)
    file_id, file_type = get_file_id(message)

    try:
        # 1. Save to Payment Registry
        payment_id = await PaymentRepository.add_payment(proj_id, message.from_user.id, file_id)

        # 2. Update Project Status
        await ProjectRepository.update_status(proj_id, ProjectStatus.AWAITING_VERIFICATION)

        # 3. Notify Student
        await message.answer(MSG_RECEIPT_RECEIVED, parse_mode="Markdown")

        # 4. Notify Admin (WITH PAYMENT ID)
        for admin_id in settings.admin_ids:
            try:
                await bot.send_message(
                    admin_id,
                    f"💰 **إيصال دفع جديد (رقم #{payment_id})**\nللمشروع: #{proj_id}",
                    parse_mode="Markdown",
                )
                if file_type == "photo":
                    await bot.send_photo(
                        admin_id,
                        file_id,
                        caption=f"verify_pay_{payment_id}",
                        reply_markup=get_payment_verify_kb(payment_id),
                    )
                else:
                    await bot.send_document(
                        admin_id,
                        file_id,
                        caption=f"verify_pay_{payment_id}",
                        reply_markup=get_payment_verify_kb(payment_id),
                    )
            except TelegramAPIError as e:
                logger.error(f"Failed to send payment receipt {payment_id} to admin {admin_id}: {e}")

        await state.clear()
    except Exception as e:
        logger.error(f"Payment upload failed: {e}", exc_info=True)
        await message.answer("⚠️ حدث خطأ أثناء رفع الإيصال. حاول مرة أخرى.")
        await state.clear()


from utils.constants import BTN_MY_PROJECTS, BTN_MY_OFFERS


@router.message(F.text == BTN_MY_PROJECTS)
@router.message(Command("my_projects"))
async def view_projects(message: types.Message):
    """
    Retrieves and displays a list of all projects owned by the user.
    Uses centralized formatting for consistent UI/UX.
    """
    # Fetch all except OFFERED which has its own menu
    projects = await ProjectRepository.get_projects_by_status(
        [ProjectStatus.PENDING, ProjectStatus.ACCEPTED, ProjectStatus.AWAITING_VERIFICATION, ProjectStatus.FINISHED, ProjectStatus.DENIED_ADMIN, ProjectStatus.DENIED_STUDENT, ProjectStatus.REJECTED_PAYMENT],
        user_id=message.from_user.id
    )

    # Generate the formatted response (handles empty lists internally)
    response = format_student_projects(projects)
    await message.answer(response, parse_mode="Markdown")


@router.message(F.text == BTN_MY_OFFERS)
@router.message(Command("my_offers"))
async def view_offers(message: types.Message):
    """Shows the student all projects where an admin has sent an offer."""
    offers = await ProjectRepository.get_projects_by_status([ProjectStatus.OFFERED], user_id=message.from_user.id)
    text = format_offer_list(offers)

    # Use new keyboard
    markup = get_offers_list_kb(offers)

    await message.answer(text, parse_mode="Markdown", reply_markup=markup)

@router.callback_query(ProjectCallback.filter(F.action == "view_offer"))
async def show_specific_offer(
    callback: types.CallbackQuery,
    callback_data: ProjectCallback
):
    proj_id = callback_data.id

    # Query the new columns!
    res = await ProjectRepository.get_project_by_id(proj_id)

    if res:
        subject = escape_md(res["subject_name"])
        price = escape_md(res["price"])
        delivery = escape_md(res["delivery_date"])

        text = MSG_OFFER_DETAILS.format(subject, price, delivery, escape_md(proj_id))

        markup = get_offer_actions_kb(proj_id)

        await callback.message.edit_text(
            text, parse_mode="Markdown", reply_markup=markup
        )
