import structlog
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
from keyboards.calendar_kb import build_calendar
from keyboards.callbacks import ProjectCallback, ProjectAction
from keyboards.factory import KeyboardFactory
from states import AdminStates
from utils.constants import (
    BTN_YES,
    BTN_NO,
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
from utils.helpers import extract_message_content, notify_admins

router = Router()
logger = structlog.get_logger(__name__)

# ── PROJECT DETAIL VIEW ─────────────────────────────────────────────────────

@router.callback_query(
    ProjectCallback.filter(F.action == ProjectAction.manage),
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
    markup = KeyboardFactory.manage_project(detail.proj_id)

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
    ProjectCallback.filter(F.action == ProjectAction.make_offer),
    F.from_user.id.in_(settings.admin_ids),
)
async def start_offer_flow(
    callback: types.CallbackQuery, state: FSMContext, callback_data: ProjectCallback
):
    proj_id = callback_data.id
    await state.update_data(offer_proj_id=proj_id)
    await callback.message.answer(MSG_ASK_PRICE.format(proj_id), reply_markup=KeyboardFactory.cancel())
    await state.set_state(AdminStates.waiting_for_price)


@router.message(AdminStates.waiting_for_price, F.from_user.id.in_(settings.admin_ids))
async def process_price(message: types.Message, state: FSMContext):
    price_text = message.text.strip()
    if not price_text:
        return await message.answer("⚠️ الرجاء إدخال سعر صالح.")
    if len(price_text) > 50:
        return await message.answer("⚠️ النص طويل جداً. الرجاء إدخال سعر مختصر (مثلاً: 50,000 ل.س).")
    await state.update_data(price=price_text)
    await message.answer(MSG_ASK_DELIVERY, reply_markup=build_calendar())
    await state.set_state(AdminStates.waiting_for_delivery)


@router.message(AdminStates.waiting_for_delivery, F.from_user.id.in_(settings.admin_ids))
async def process_delivery(message: types.Message, state: FSMContext):
    delivery_text = message.text.strip()
    if not delivery_text:
        return await message.answer("⚠️ الرجاء إدخال موعد صالح.")
    if len(delivery_text) > 50:
        return await message.answer("⚠️ النص طويل جداً. حاول الاختصار (مثلاً: 2024-05-01).")
    await state.update_data(delivery=delivery_text)
    await message.answer(MSG_ASK_NOTES, reply_markup=KeyboardFactory.notes_decision())
    await state.set_state(AdminStates.waiting_for_notes_decision)


@router.message(AdminStates.waiting_for_notes_decision, F.from_user.id.in_(settings.admin_ids))
async def process_notes_decision(
    message: types.Message, state: FSMContext, bot, project_repo: ProjectRepository
):
    text = message.text.strip()
    if text == BTN_YES:
        await message.answer(MSG_ASK_NOTES_TEXT, reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(AdminStates.waiting_for_notes_text)
    elif text == BTN_NO:
        await _finalize_offer(message, state, bot, project_repo, notes=MSG_NO_NOTES)
    else:
        await message.answer("⚠️ الرجاء اختيار 'نعم' أو 'لا' من لوحة المفاتيح المرفقة.", reply_markup=KeyboardFactory.notes_decision())


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
        
        await bot.send_chat_action(result.user_id, "typing")
        
        await bot.send_message(
            result.user_id, offer_text, parse_mode="Markdown",
            reply_markup=KeyboardFactory.offer_actions(result.proj_id),
        )
        await message.answer(MSG_OFFER_SENT, reply_markup=types.ReplyKeyboardRemove())
        await state.clear()
    except Exception as e:
        logger.error("Failed to send offer", project_id=proj_id, error=str(e), exc_info=True)
        await message.answer("⚠️ حدث خطأ أثناء إرسال العرض.", reply_markup=types.ReplyKeyboardRemove())
        await state.clear()


# ── WORK LIFECYCLE ──────────────────────────────────────────────────────────

@router.callback_query(
    ProjectCallback.filter(F.action == ProjectAction.manage_accepted),
    F.from_user.id.in_(settings.admin_ids),
)
async def manage_accepted_project(
    callback: types.CallbackQuery, state: FSMContext, callback_data: ProjectCallback
):
    proj_id = callback_data.id
    await state.update_data(finish_proj_id=proj_id)
    await state.set_state(AdminStates.waiting_for_finished_work)
    await callback.message.answer(MSG_UPLOAD_FINISHED_WORK.format(proj_id), reply_markup=KeyboardFactory.cancel())
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
        text, file_id, file_type = extract_message_content(message)
        if file_id:
            # Dispatch the media to the student using the _dispatch pattern
            methods = {
                "photo": bot.send_photo,
                "video": bot.send_video,
                "document": bot.send_document,
                "audio": bot.send_audio,
                "voice": bot.send_voice,
            }
            send_method = methods.get(file_type, bot.send_document)
            media_kwarg = {file_type or "document": file_id}
            await send_method(result.user_id, **media_kwarg, caption=message.caption)
        else:
            text = message.text or "✅ تم رفع ملف بدون رسالة نصية."
            await bot.send_message(result.user_id, text)
        await message.answer(MSG_FINISHED_CONFIRM.format(result.proj_id), reply_markup=types.ReplyKeyboardRemove())
    except Exception as e:
        logger.error("Failed to finish project", project_id=proj_id, error=str(e), exc_info=True)
        await message.answer("⚠️ حدث خطأ أثناء إنهاء المشروع.")
    await state.clear()


# ── DENY (admin + student) ──────────────────────────────────────────────────

@router.callback_query(ProjectCallback.filter(F.action == ProjectAction.deny))
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
            await notify_admins(bot, MSG_PROJECT_DENIED_STUDENT_TO_ADMIN.format(proj_id))
    except PermissionError as e:
        return await callback.answer(f"⚠️ {e}", show_alert=True)

    await callback.answer()
    try:
        await callback.message.edit_text(MSG_PROJECT_CLOSED.format(proj_id))
    except Exception:
        # Message already shows the closed state (e.g. repeated test run)
        pass
