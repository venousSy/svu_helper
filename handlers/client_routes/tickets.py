"""
Client Ticket Handlers
======================
Student-facing UI for the support ticket system:
  - Support menu (open ticket / list active tickets)
  - FSM: compose new ticket message
  - View ticket conversation history (paginated)
  - Reply to an open ticket
  - Close a ticket
"""
import math
from typing import Optional

from aiogram import Bot, F, Router, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext

import structlog

from config import settings
from keyboards.callbacks import (
    MenuAction,
    MenuCallback,
    PageAction,
    PageCallback,
    TicketAction,
    TicketCallback,
)
from keyboards.factory import KeyboardFactory
from infrastructure.repositories.ticket import TicketRepository
from services.ticket_service import TicketService
from states import TicketStates

logger = structlog.get_logger()
router = Router()

MESSAGES_PER_PAGE = 10


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def _build_ticket_service(
    ticket_repo: TicketRepository, bot: Bot
) -> TicketService:
    forum_id = getattr(settings, "ADMIN_FORUM_GROUP_ID", None)
    return TicketService(
        ticket_repo=ticket_repo, bot=bot, forum_group_id=forum_id
    )


def _extract_content(message: types.Message):
    """Extract text and file info from a user message."""
    text: Optional[str] = None
    file_id: Optional[str] = None
    file_type: Optional[str] = None

    if message.photo:
        file_id = message.photo[-1].file_id
        file_type = "photo"
        text = message.caption
    elif message.document:
        file_id = message.document.file_id
        file_type = "document"
        text = message.caption
    elif message.video:
        file_id = message.video.file_id
        file_type = "video"
        text = message.caption
    elif message.text:
        text = message.text

    return text, file_id, file_type


def _format_messages(messages: list) -> str:
    """Format a list of message dicts into a readable conversation."""
    if not messages:
        return "📭 لا توجد رسائل بعد."

    lines = []
    for msg in messages:
        sender = "👤 أنت" if msg["sender"] == "user" else "🛡 الدعم"
        ts = msg.get("timestamp", "")
        if hasattr(ts, "strftime"):
            ts = ts.strftime("%m/%d %H:%M")
        else:
            ts = str(ts)[:16]

        content_parts = []
        if msg.get("text"):
            content_parts.append(msg["text"])
        if msg.get("file_id"):
            ft = msg.get("file_type", "ملف")
            content_parts.append(f"[📎 {ft}]")

        content = " ".join(content_parts) if content_parts else "[رسالة فارغة]"
        lines.append(f"<b>{sender}</b> <i>({ts})</i>:\n<blockquote>{content}</blockquote>")

    return "\n\n".join(lines)


# ------------------------------------------------------------------
# Support Menu
# ------------------------------------------------------------------
@router.callback_query(MenuCallback.filter(F.action == MenuAction.support))
async def show_support_menu(callback: types.CallbackQuery, state: FSMContext):
    """Show the support sub-menu."""
    await state.clear()
    await callback.message.edit_text(
        "📩 <b>الدعم الفني</b>\n\n"
        "يمكنك فتح تذكرة جديدة أو متابعة تذاكرك المفتوحة.",
        reply_markup=KeyboardFactory.support_menu(),
        parse_mode="HTML",
    )
    await callback.answer()


# ------------------------------------------------------------------
# Open New Ticket
# ------------------------------------------------------------------
@router.callback_query(
    TicketCallback.filter(F.action == TicketAction.open_new)
)
async def start_new_ticket(
    callback: types.CallbackQuery, state: FSMContext
):
    """Prompt user to type/send their support message."""
    await state.set_state(TicketStates.waiting_for_message)
    await callback.message.edit_text(
        "✏️ <b>فتح تذكرة جديدة</b>\n\n"
        "أرسل رسالتك أو صورة/ملف يوضح مشكلتك.",
        reply_markup=KeyboardFactory.inline_cancel_ticket_action(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(TicketStates.waiting_for_message)
async def receive_new_ticket_message(
    message: types.Message,
    state: FSMContext,
    ticket_repo: TicketRepository,
    bot: Bot,
):
    """Capture the initial ticket message, create ticket + forum topic."""
    text, file_id, file_type = _extract_content(message)

    if not text and not file_id:
        await message.answer(
            "⚠️ أرسل نصاً أو صورة/ملف لفتح التذكرة."
        )
        return

    service = _build_ticket_service(ticket_repo, bot)
    ticket_id = await service.open_ticket(
        user_id=message.from_user.id,
        username=message.from_user.username,
        user_full_name=message.from_user.full_name,
        text=text,
        file_id=file_id,
        file_type=file_type,
    )

    await state.clear()
    await message.answer(
        f"✅ <b>تم فتح التذكرة #{ticket_id} بنجاح!</b>\n\n"
        "سيتم الرد عليك في أقرب وقت.\n"
        "يمكنك متابعة التذكرة من قائمة الدعم الفني.",
        reply_markup=KeyboardFactory.support_menu(),
        parse_mode="HTML",
    )


# ------------------------------------------------------------------
# Cancel Action (Generic for all ticket input states)
# ------------------------------------------------------------------
@router.callback_query(
    TicketCallback.filter(F.action == TicketAction.cancel_action)
)
async def cancel_ticket_action(
    callback: types.CallbackQuery, state: FSMContext
):
    """Cancel the current FSM state and return to support menu."""
    await state.clear()
    await callback.message.edit_text(
        "تم إلغاء العملية.\n\n"
        "📩 <b>الدعم الفني</b>\n"
        "يمكنك فتح تذكرة جديدة أو متابعة تذاكرك المفتوحة.",
        reply_markup=KeyboardFactory.support_menu(),
        parse_mode="HTML",
    )
    await callback.answer("تم الإلغاء")


# ------------------------------------------------------------------
# List Active Tickets
# ------------------------------------------------------------------
@router.callback_query(
    TicketCallback.filter(F.action == TicketAction.list_active)
)
async def list_active_tickets(
    callback: types.CallbackQuery,
    ticket_repo: TicketRepository,
    bot: Bot,
):
    """Show the user's open tickets."""
    service = _build_ticket_service(ticket_repo, bot)
    tickets = await service.get_user_active_tickets(callback.from_user.id)

    if not tickets:
        try:
            await callback.message.edit_text(
                "📭 <b>لا توجد تذاكر مفتوحة حالياً.</b>\n\n"
                "يمكنك فتح تذكرة جديدة من القائمة.",
                reply_markup=KeyboardFactory.support_menu(),
                parse_mode="HTML",
            )
        except TelegramBadRequest:
            pass  # message content unchanged — ignore
        await callback.answer()
        return

    await callback.message.edit_text(
        f"📋 <b>تذاكرك المفتوحة ({len(tickets)})</b>\n\n"
        "اختر تذكرة لعرض المحادثة:",
        reply_markup=KeyboardFactory.active_tickets_list(tickets),
        parse_mode="HTML",
    )
    await callback.answer()


# ------------------------------------------------------------------
# View Ticket Detail
# ------------------------------------------------------------------
@router.callback_query(
    TicketCallback.filter(F.action == TicketAction.view)
)
async def view_ticket(
    callback: types.CallbackQuery,
    callback_data: TicketCallback,
    ticket_repo: TicketRepository,
    bot: Bot,
    state: FSMContext,
):
    """Show the ticket detail with recent messages."""
    service = _build_ticket_service(ticket_repo, bot)
    ticket = await service.get_ticket(callback_data.id)

    if not ticket:
        await callback.answer("❌ التذكرة غير موجودة.", show_alert=True)
        return

    # Store ticket_id in FSM data for pagination
    await state.update_data(viewing_ticket_id=callback_data.id)

    messages = await service.get_conversation_history(
        callback_data.id, page=0, page_size=MESSAGES_PER_PAGE
    )
    total = await service.get_message_count(callback_data.id)
    total_pages = max(1, math.ceil(total / MESSAGES_PER_PAGE))

    status_label = "🟢 مفتوحة" if ticket["status"] == "open" else "🔴 مغلقة"
    is_closed = ticket["status"] == "closed"

    header = (
        f"🎫 <b>تذكرة #{callback_data.id}</b>  |  {status_label}\n"
        f"{'─' * 28}\n\n"
    )
    body = _format_messages(messages)

    if total_pages > 1:
        footer = f"\n\n📄 صفحة 1/{total_pages}  |  إجمالي الرسائل: {total}"
        kb = KeyboardFactory.ticket_message_pagination(
            callback_data.id, 0, total_pages
        )
    else:
        footer = ""
        kb = KeyboardFactory.ticket_detail(
            callback_data.id, is_closed=is_closed
        )

    await callback.message.edit_text(
        f"{header}{body}{footer}",
        reply_markup=kb,
        parse_mode="HTML",
    )
    await callback.answer()


# ------------------------------------------------------------------
# Paginate Ticket Messages
# ------------------------------------------------------------------
@router.callback_query(
    PageCallback.filter(F.action == PageAction.ticket_messages)
)
async def paginate_ticket_messages(
    callback: types.CallbackQuery,
    callback_data: PageCallback,
    ticket_repo: TicketRepository,
    bot: Bot,
    state: FSMContext,
):
    """Navigate through ticket message pages."""
    data = await state.get_data()
    ticket_id = data.get("viewing_ticket_id")
    if not ticket_id:
        await callback.answer("⚠️ حدث خطأ. أعد فتح التذكرة.", show_alert=True)
        return

    page = callback_data.page
    service = _build_ticket_service(ticket_repo, bot)

    messages = await service.get_conversation_history(
        ticket_id, page=page, page_size=MESSAGES_PER_PAGE
    )
    total = await service.get_message_count(ticket_id)
    total_pages = max(1, math.ceil(total / MESSAGES_PER_PAGE))

    header = (
        f"🎫 <b>تذكرة #{ticket_id}</b>\n"
        f"{'─' * 28}\n\n"
    )
    body = _format_messages(messages)
    footer = f"\n\n📄 صفحة {page + 1}/{total_pages}  |  إجمالي الرسائل: {total}"

    kb = KeyboardFactory.ticket_message_pagination(
        ticket_id, page, total_pages
    )

    await callback.message.edit_text(
        f"{header}{body}{footer}",
        reply_markup=kb,
        parse_mode="HTML",
    )
    await callback.answer()


# ------------------------------------------------------------------
# Reply to Ticket
# ------------------------------------------------------------------
@router.callback_query(
    TicketCallback.filter(F.action == TicketAction.reply)
)
async def start_ticket_reply(
    callback: types.CallbackQuery,
    callback_data: TicketCallback,
    state: FSMContext,
):
    """Set FSM to capture the user's reply."""
    await state.set_state(TicketStates.waiting_for_reply)
    await state.update_data(reply_ticket_id=callback_data.id)
    await callback.message.edit_text(
        f"✏️ <b>الرد على تذكرة #{callback_data.id}</b>\n\n"
        "أرسل رسالتك أو صورة/ملف.",
        reply_markup=KeyboardFactory.inline_cancel_ticket_action(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(TicketStates.waiting_for_reply)
async def receive_ticket_reply(
    message: types.Message,
    state: FSMContext,
    ticket_repo: TicketRepository,
    bot: Bot,
):
    """Capture the reply and forward to the admin topic."""
    data = await state.get_data()
    ticket_id = data.get("reply_ticket_id")
    if not ticket_id:
        await state.clear()
        await message.answer("⚠️ حدث خطأ. حاول مرة أخرى.")
        return

    text, file_id, file_type = _extract_content(message)

    if not text and not file_id:
        await message.answer("⚠️ أرسل نصاً أو صورة/ملف للرد.")
        return

    service = _build_ticket_service(ticket_repo, bot)
    success = await service.user_reply(
        ticket_id,
        text=text,
        file_id=file_id,
        file_type=file_type,
    )

    await state.clear()

    if success:
        await message.answer(
            f"✅ تم إرسال ردك على التذكرة #{ticket_id}.",
            reply_markup=KeyboardFactory.support_menu(),
        )
    else:
        await message.answer(
            "❌ التذكرة غير موجودة أو مغلقة.",
            reply_markup=KeyboardFactory.support_menu(),
        )


# ------------------------------------------------------------------
# Close Ticket
# ------------------------------------------------------------------
@router.callback_query(
    TicketCallback.filter(F.action == TicketAction.close)
)
async def close_ticket_handler(
    callback: types.CallbackQuery,
    callback_data: TicketCallback,
    ticket_repo: TicketRepository,
    bot: Bot,
):
    """Close a ticket by user request."""
    service = _build_ticket_service(ticket_repo, bot)
    success = await service.close_ticket(callback_data.id)

    if success:
        await callback.message.edit_text(
            f"🔒 <b>تم إغلاق التذكرة #{callback_data.id}.</b>\n\n"
            "شكراً لتواصلك مع الدعم الفني!",
            reply_markup=KeyboardFactory.support_menu(),
            parse_mode="HTML",
        )
    else:
        await callback.answer("❌ خطأ في إغلاق التذكرة.", show_alert=True)

    await callback.answer()


# ------------------------------------------------------------------
# List Closed Tickets (History)
# ------------------------------------------------------------------
@router.callback_query(
    TicketCallback.filter(F.action == TicketAction.list_closed)
)
async def list_closed_tickets(
    callback: types.CallbackQuery,
    ticket_repo: TicketRepository,
    bot: Bot,
):
    """Show the user's closed tickets history."""
    service = _build_ticket_service(ticket_repo, bot)
    tickets = await service.get_user_closed_tickets(callback.from_user.id)

    if not tickets:
        try:
            await callback.message.edit_text(
                "📭 <b>لا توجد تذاكر مغلقة.</b>\n\n"
                "سجل التذاكر المغلقة سيظهر هنا بعد إغلاق تذكرة.",
                reply_markup=KeyboardFactory.support_menu(),
                parse_mode="HTML",
            )
        except TelegramBadRequest:
            pass
        await callback.answer()
        return

    try:
        await callback.message.edit_text(
            f"📜 <b>التذاكر المغلقة ({len(tickets)})</b>\n\n"
            "اختر تذكرة لعرض المحادثة أو إعادة فتحها:",
            reply_markup=KeyboardFactory.closed_tickets_list(tickets),
            parse_mode="HTML",
        )
    except TelegramBadRequest:
        pass
    await callback.answer()


# ------------------------------------------------------------------
# Reopen a Closed Ticket
# ------------------------------------------------------------------
@router.callback_query(
    TicketCallback.filter(F.action == TicketAction.reopen)
)
async def reopen_ticket_handler(
    callback: types.CallbackQuery,
    callback_data: TicketCallback,
    ticket_repo: TicketRepository,
    bot: Bot,
):
    """Reopen a closed ticket by user request."""
    service = _build_ticket_service(ticket_repo, bot)
    success = await service.reopen_ticket(callback_data.id)

    if success:
        await callback.message.edit_text(
            f"🔓 <b>تم إعادة فتح التذكرة #{callback_data.id}.</b>\n\n"
            "يمكنك الآن الرد عليها من جديد.",
            reply_markup=KeyboardFactory.support_menu(),
            parse_mode="HTML",
        )
    else:
        await callback.answer("❌ خطأ في إعادة فتح التذكرة.", show_alert=True)

    await callback.answer()
