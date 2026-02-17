import logging
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from config import settings
from database.repositories import ProjectRepository
from keyboards.admin_kb import (
    get_cancel_kb,
    get_manage_project_kb,
    get_notes_decision_kb,
)
from keyboards.client_kb import get_offer_actions_kb
from keyboards.callbacks import ProjectCallback
from states import AdminStates
from utils.constants import (
    BTN_YES,
    MSG_ASK_DELIVERY,
    MSG_ASK_NOTES,
    MSG_ASK_NOTES_TEXT,
    MSG_ASK_PRICE,
    MSG_FINISHED_CONFIRM,
    MSG_NO_NOTES,
    MSG_OFFER_SENT,
    MSG_PROJECT_CLOSED,
    MSG_PROJECT_DENIED_CLIENT,
    MSG_PROJECT_DENIED_STUDENT_TO_ADMIN,
    MSG_PROJECT_DETAILS_HEADER,
    MSG_UPLOAD_FINISHED_WORK,
    MSG_WORK_FINISHED_ALERT,
)
from utils.enums import ProjectStatus
from utils.formatters import escape_md
from utils.helpers import get_file_id

router = Router()
logger = logging.getLogger(__name__)

# --- PROJECT MANAGEMENT & OFFER FLOW ---

@router.callback_query(
    ProjectCallback.filter(F.action == "manage"),
    F.from_user.id.in_(settings.ADMIN_IDS),
)
async def view_project_details(
    callback: types.CallbackQuery, 
    callback_data: ProjectCallback
):
    """Displays detailed project specs and original file for admin review."""
    proj_id = callback_data.id
    project = await ProjectRepository.get_project_by_id(proj_id)
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


@router.callback_query(ProjectCallback.filter(F.action == "make_offer"), F.from_user.id.in_(settings.ADMIN_IDS))
async def start_offer_flow(
    callback: types.CallbackQuery, 
    state: FSMContext, 
    callback_data: ProjectCallback
):
    """Starts a step-by-step FSM to collect price and delivery data."""
    proj_id = callback_data.id
    await state.update_data(offer_proj_id=proj_id)
    await callback.message.answer(
        MSG_ASK_PRICE.format(proj_id), reply_markup=get_cancel_kb()
    )
    await state.set_state(AdminStates.waiting_for_price)


@router.message(AdminStates.waiting_for_price, F.from_user.id.in_(settings.ADMIN_IDS))
async def process_price(message: types.Message, state: FSMContext):
    """Stores price and requests delivery date."""
    price_text = message.text.strip()

    # VALIDATION
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


@router.message(AdminStates.waiting_for_delivery, F.from_user.id.in_(settings.ADMIN_IDS))
async def process_delivery(message: types.Message, state: FSMContext):
    """Stores delivery date and asks if extra notes are needed."""
    delivery_text = message.text.strip()

    if not delivery_text:
        await message.answer("⚠️ الرجاء إدخال موعد صالح.")
        return

    if len(delivery_text) > 50:
        await message.answer("⚠️ النص طويل جداً. حاول الاختصار (مثلاً: 2024-05-01).")
        return

    await state.update_data(delivery=delivery_text)

    await message.answer(MSG_ASK_NOTES, reply_markup=get_notes_decision_kb())
    await state.set_state(AdminStates.waiting_for_notes_decision)


@router.message(AdminStates.waiting_for_notes_decision, F.from_user.id.in_(settings.ADMIN_IDS))
async def process_notes_decision(message: types.Message, state: FSMContext, bot):
    """Branches FSM based on whether the admin wants to add custom notes."""
    if message.text == BTN_YES:
        await message.answer(
            MSG_ASK_NOTES_TEXT, reply_markup=types.ReplyKeyboardRemove()
        )
        await state.set_state(AdminStates.waiting_for_notes_text)
    else:
        await finalize_and_send_offer(message, state, bot, notes_text=MSG_NO_NOTES)


@router.message(AdminStates.waiting_for_notes_text, F.from_user.id.in_(settings.ADMIN_IDS))
async def process_notes_text(message: types.Message, state: FSMContext, bot):
    """Captures final notes and triggers the student notification."""
    await finalize_and_send_offer(message, state, bot, notes_text=message.text)


async def finalize_and_send_offer(
    message: types.Message, state: FSMContext, bot, notes_text: str
):
    """Compiles all collected data into a structured offer and sends it to the student."""
    data = await state.get_data()
    proj_id = data["offer_proj_id"]
    res = await ProjectRepository.get_project_by_id(proj_id)

    try:
        if res:
            await ProjectRepository.update_offer(proj_id, data["price"], data["delivery"])
            await ProjectRepository.update_status(proj_id, ProjectStatus.OFFERED)
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
    ProjectCallback.filter(F.action == "manage_accepted"), 
    F.from_user.id.in_(settings.ADMIN_IDS)
)
async def manage_accepted_project(
    callback: types.CallbackQuery, 
    state: FSMContext,
    callback_data: ProjectCallback
):
    """Prepares FSM to receive the final project file from the admin."""
    proj_id = callback_data.id
    await state.update_data(finish_proj_id=proj_id)
    await state.set_state(AdminStates.waiting_for_finished_work)
    await callback.message.answer(
        MSG_UPLOAD_FINISHED_WORK.format(proj_id), reply_markup=get_cancel_kb()
    )
    await callback.answer()


@router.message(AdminStates.waiting_for_finished_work, F.from_user.id.in_(settings.ADMIN_IDS))
async def process_finished_work(message: types.Message, state: FSMContext, bot):
    """Transfers the final work from admin to student and marks project as 'Finished'."""
    data = await state.get_data()
    proj_id = data.get("finish_proj_id")
    res = await ProjectRepository.get_project_by_id(proj_id)

    if res:
        u_id = res["user_id"]
        sub = escape_md(res["subject_name"])

        await bot.send_message(
            u_id, MSG_WORK_FINISHED_ALERT.format(sub, proj_id), parse_mode="Markdown"
        )

        # Relay the actual content 
        file_id, file_type = get_file_id(message)
        if file_type == "document":
            await bot.send_document(u_id, file_id, caption=message.caption)
        elif file_type == "photo":
            await bot.send_photo(u_id, file_id, caption=message.caption)
        else:
            await bot.send_message(u_id, message.text)

        await ProjectRepository.update_status(proj_id, ProjectStatus.FINISHED)
        await message.answer(
            MSG_FINISHED_CONFIRM.format(proj_id),
            reply_markup=types.ReplyKeyboardRemove(),
        )

    await state.clear()


@router.callback_query(ProjectCallback.filter(F.action == "deny"))
async def handle_deny(
    callback: types.CallbackQuery, 
    bot,
    callback_data: ProjectCallback
):
    """General denial handler for both Admin rejection and Student cancellation."""
    proj_id = callback_data.id
    if callback.from_user.id in settings.ADMIN_IDS:
        await ProjectRepository.update_status(proj_id, ProjectStatus.DENIED_ADMIN)
        res = await ProjectRepository.get_project_by_id(proj_id)
        if res:
            await bot.send_message(
                res["user_id"], MSG_PROJECT_DENIED_CLIENT.format(proj_id)
            )
    else:
        await ProjectRepository.update_status(proj_id, ProjectStatus.DENIED_STUDENT)
        for admin_id in ADMIN_IDS:
             await bot.send_message(
                admin_id, MSG_PROJECT_DENIED_STUDENT_TO_ADMIN.format(proj_id)
            )

    await callback.message.edit_text(MSG_PROJECT_CLOSED.format(proj_id))
