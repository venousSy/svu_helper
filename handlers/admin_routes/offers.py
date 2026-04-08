import logging
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from application.offer_service import (
    DenyProjectService,
    FinishProjectService,
    GetProjectDetailService,
    SendOfferService,
)
from config import settings
from infrastructure.repositories import ProjectRepository
from keyboards.admin_kb import get_cancel_kb, get_manage_project_kb, get_notes_decision_kb
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
from utils.formatters import escape_md
from utils.helpers import get_file_id

router = Router()
logger = logging.getLogger(__name__)

# ── PROJECT DETAIL VIEW ─────────────────────────────────────────────────────

@router.callback_query(
    ProjectCallback.filter(F.action == "manage"),
    F.from_user.id.in_(settings.admin_ids),
)
async def view_project_details(
    callback: types.CallbackQuery,
    callback_data: ProjectCallback,
    project_repo: ProjectRepository,
):
    detail = await GetProjectDetailService(project_repo).execute(callback_data.id)
    if not detail:
        return

    user_line = f"👤 [{escape_md(detail.user_full_name)}](tg://user?id={detail.user_id})"
    if detail.username:
        user_line += f" (@{escape_md(detail.username)})"

    text = (
        MSG_PROJECT_DETAILS_HEADER.format(detail.proj_id) + "\n"
        f"{user_line}\n"
        f"*المادة:* {escape_md(detail.subject)}\n"
        f"*المدرس:* {escape_md(detail.tutor)}\n"
        f"*الموعد:* {escape_md(detail.deadline)}\n"
        f"*التفاصيل:* {escape_md(detail.details)}"
    )
    markup = get_manage_project_kb(detail.proj_id)

    if detail.file_id:
        if len(text) > 1024:
            header = f"📁 *المشروع #{detail.proj_id}* (التفاصيل في الرسالة التالية)"
            await _send_media_safely(callback, detail.file_id, detail.file_type, header, markup=None)
            try:
                await callback.message.answer(text, parse_mode="Markdown", reply_markup=markup)
            except Exception:
                await callback.message.answer(text, parse_mode=None, reply_markup=markup)
            await callback.message.delete()
        else:
            success = await _send_media_safely(callback, detail.file_id, detail.file_type, text, markup=markup)
            if success:
                await callback.message.delete()
    else:
        try:
            await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=markup)
        except Exception:
            await callback.message.edit_text(text, parse_mode=None, reply_markup=markup)


async def _send_media_safely(callback, file_id, file_type, caption, markup) -> bool:
    """Sends a media file with robust multi-level fallback."""
    methods = {
        "photo": callback.message.answer_photo,
        "video": callback.message.answer_video,
        "document": callback.message.answer_document,
        "audio": callback.message.answer_audio,
        "voice": callback.message.answer_voice,
    }
    if file_type and file_type in methods:
        try:
            await methods[file_type](file_id, caption=caption, parse_mode="Markdown", reply_markup=markup)
            return True
        except Exception:
            try:
                await methods[file_type](file_id, caption=caption, parse_mode=None, reply_markup=markup)
                return True
            except Exception:
                pass
    for method in [callback.message.answer_photo, callback.message.answer_document, callback.message.answer_video]:
        try:
            await method(file_id, caption=caption, parse_mode="Markdown", reply_markup=markup)
            return True
        except Exception:
            try:
                await method(file_id, caption=caption, parse_mode=None, reply_markup=markup)
                return True
            except Exception:
                continue
    try:
        await callback.message.answer_document(
            file_id,
            caption="⚠️ لم نتمكن من عرض التفاصيل (مشكلة في صيغة الرسالة).",
            reply_markup=markup,
        )
        return True
    except Exception as e:
        await callback.answer(f"Error: {str(e)}", show_alert=True)
        return False


# ── OFFER FLOW (FSM) ────────────────────────────────────────────────────────

@router.callback_query(
    ProjectCallback.filter(F.action == "make_offer"),
    F.from_user.id.in_(settings.admin_ids),
)
async def start_offer_flow(
    callback: types.CallbackQuery, state: FSMContext, callback_data: ProjectCallback
):
    proj_id = callback_data.id
    await state.update_data(offer_proj_id=proj_id)
    await callback.message.answer(MSG_ASK_PRICE.format(proj_id), reply_markup=get_cancel_kb())
    await state.set_state(AdminStates.waiting_for_price)


@router.message(AdminStates.waiting_for_price, F.from_user.id.in_(settings.admin_ids))
async def process_price(message: types.Message, state: FSMContext):
    price_text = message.text.strip()
    if not price_text:
        return await message.answer("⚠️ الرجاء إدخال سعر صالح.")
    if len(price_text) > 50:
        return await message.answer("⚠️ النص طويل جداً. الرجاء إدخال سعر مختصر (مثلاً: 50,000 ل.س).")
    await state.update_data(price=price_text)
    await message.answer(MSG_ASK_DELIVERY, reply_markup=get_cancel_kb())
    await state.set_state(AdminStates.waiting_for_delivery)


@router.message(AdminStates.waiting_for_delivery, F.from_user.id.in_(settings.admin_ids))
async def process_delivery(message: types.Message, state: FSMContext):
    delivery_text = message.text.strip()
    if not delivery_text:
        return await message.answer("⚠️ الرجاء إدخال موعد صالح.")
    if len(delivery_text) > 50:
        return await message.answer("⚠️ النص طويل جداً. حاول الاختصار (مثلاً: 2024-05-01).")
    await state.update_data(delivery=delivery_text)
    await message.answer(MSG_ASK_NOTES, reply_markup=get_notes_decision_kb())
    await state.set_state(AdminStates.waiting_for_notes_decision)


@router.message(AdminStates.waiting_for_notes_decision, F.from_user.id.in_(settings.admin_ids))
async def process_notes_decision(
    message: types.Message, state: FSMContext, bot, project_repo: ProjectRepository
):
    if message.text == BTN_YES:
        await message.answer(MSG_ASK_NOTES_TEXT, reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(AdminStates.waiting_for_notes_text)
    else:
        await _finalize_offer(message, state, bot, project_repo, notes=MSG_NO_NOTES)


@router.message(AdminStates.waiting_for_notes_text, F.from_user.id.in_(settings.admin_ids))
async def process_notes_text(
    message: types.Message, state: FSMContext, bot, project_repo: ProjectRepository
):
    await _finalize_offer(message, state, bot, project_repo, notes=message.text)


async def _finalize_offer(message, state, bot, project_repo, notes: str):
    """Calls SendOfferService and relays the offer to the student."""
    data = await state.get_data()
    proj_id = data["offer_proj_id"]
    try:
        result = await SendOfferService(project_repo).execute(
            proj_id=proj_id,
            price=data["price"],
            delivery=data["delivery"],
            notes=notes,
        )
        offer_text = (
            f"🎁 **عرض جديد لمشروع: {escape_md(result.subject)}!**\n━━━━━━━━━━━━━\n"
            f"💰 **السعر:** {escape_md(result.price)}\n"
            f"📅 **التسليم:** {escape_md(result.delivery)}\n"
            f"📝 **ملاحظات:** {escape_md(result.notes)}\n━━━━━━━━━━━━━"
        )
        await bot.send_message(
            result.user_id, offer_text, parse_mode="Markdown",
            reply_markup=get_offer_actions_kb(result.proj_id),
        )
        await message.answer(MSG_OFFER_SENT, reply_markup=types.ReplyKeyboardRemove())
        await state.clear()
    except Exception as e:
        logger.error(f"Failed to send offer for #{proj_id}: {e}", exc_info=True)
        await message.answer("⚠️ حدث خطأ أثناء إرسال العرض.", reply_markup=types.ReplyKeyboardRemove())
        await state.clear()


# ── WORK LIFECYCLE ──────────────────────────────────────────────────────────

@router.callback_query(
    ProjectCallback.filter(F.action == "manage_accepted"),
    F.from_user.id.in_(settings.admin_ids),
)
async def manage_accepted_project(
    callback: types.CallbackQuery, state: FSMContext, callback_data: ProjectCallback
):
    proj_id = callback_data.id
    await state.update_data(finish_proj_id=proj_id)
    await state.set_state(AdminStates.waiting_for_finished_work)
    await callback.message.answer(MSG_UPLOAD_FINISHED_WORK.format(proj_id), reply_markup=get_cancel_kb())
    await callback.answer()


@router.message(AdminStates.waiting_for_finished_work, F.from_user.id.in_(settings.admin_ids))
async def process_finished_work(
    message: types.Message, state: FSMContext, bot, project_repo: ProjectRepository
):
    """FinishProjectService marks the project done; handler relays the file."""
    data = await state.get_data()
    proj_id = data.get("finish_proj_id")
    try:
        result = await FinishProjectService(project_repo).execute(proj_id)
        await bot.send_message(
            result.user_id,
            MSG_WORK_FINISHED_ALERT.format(escape_md(result.subject), result.proj_id),
            parse_mode="Markdown",
        )
        file_id, file_type = get_file_id(message)
        if file_type == "document":
            await bot.send_document(result.user_id, file_id, caption=message.caption)
        elif file_type == "photo":
            await bot.send_photo(result.user_id, file_id, caption=message.caption)
        elif file_type == "video":
            await bot.send_video(result.user_id, file_id, caption=message.caption)
        elif file_type == "audio":
            await bot.send_audio(result.user_id, file_id, caption=message.caption)
        elif file_type == "voice":
            await bot.send_voice(result.user_id, file_id, caption=message.caption)
        else:
            text = message.text or "✅ تم رفع ملف بدون رسالة نصية."
            await bot.send_message(result.user_id, text)
        await message.answer(MSG_FINISHED_CONFIRM.format(result.proj_id), reply_markup=types.ReplyKeyboardRemove())
    except Exception as e:
        logger.error(f"Failed to finish project #{proj_id}: {e}", exc_info=True)
        await message.answer("⚠️ حدث خطأ أثناء إنهاء المشروع.")
    await state.clear()


# ── DENY (admin + student) ──────────────────────────────────────────────────

@router.callback_query(ProjectCallback.filter(F.action == "deny"))
async def handle_deny(
    callback: types.CallbackQuery,
    bot,
    callback_data: ProjectCallback,
    project_repo: ProjectRepository,
):
    """DenyProjectService handles auth + status transition; handler sends notifications."""
    proj_id = callback_data.id
    service = DenyProjectService(project_repo)

    try:
        if callback.from_user.id in settings.admin_ids:
            result = await service.execute_admin_deny(proj_id)
            if result.student_user_id:
                await bot.send_message(result.student_user_id, MSG_PROJECT_DENIED_CLIENT.format(proj_id))
        else:
            result = await service.execute_student_deny(proj_id, callback.from_user.id)
            for admin_id in settings.admin_ids:
                await bot.send_message(admin_id, MSG_PROJECT_DENIED_STUDENT_TO_ADMIN.format(proj_id))
    except PermissionError as e:
        return await callback.answer(f"⚠️ {e}", show_alert=True)

    await callback.answer()
    try:
        await callback.message.edit_text(MSG_PROJECT_CLOSED.format(proj_id))
    except Exception:
        # Message already shows the closed state (e.g. repeated test run)
        pass
