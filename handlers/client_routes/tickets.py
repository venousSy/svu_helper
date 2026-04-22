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
from states import TicketStates
from utils.constants import (
    MSG_TICKET_CANCEL_ANSWER,
    MSG_TICKET_CANCELLED,
    MSG_TICKET_CLOSE_ERROR,
    MSG_TICKET_CLOSED_CONFIRM,
    MSG_TICKET_CLOSED_HEADER,
    MSG_TICKET_CLOSED_OR_MISSING,
    MSG_TICKET_CREATED,
    MSG_TICKET_EMPTY_MESSAGE,
    MSG_TICKET_ERROR_REOPEN,
    MSG_TICKET_FILE_LABEL,
    MSG_TICKET_NEW_PROMPT,
    MSG_TICKET_NO_CLOSED,
    MSG_TICKET_NO_MESSAGES,
    MSG_TICKET_NO_OPEN,
    MSG_TICKET_NOT_FOUND,
    MSG_TICKET_OPEN_HEADER,
    MSG_TICKET_PAGE_FOOTER,
    MSG_TICKET_REOPEN_ERROR,
    MSG_TICKET_REOPENED,
    MSG_TICKET_REPLY_ERROR,
    MSG_TICKET_REPLY_PROMPT,
    MSG_TICKET_REPLY_SUCCESS,
    MSG_TICKET_SEND_REPLY,
    MSG_TICKET_SEND_TEXT,
    MSG_TICKET_SENDER_SUPPORT,
    MSG_TICKET_SENDER_USER,
    MSG_TICKET_STATUS_CLOSED,
    MSG_TICKET_STATUS_OPEN,
    MSG_TICKET_SUPPORT_HUB,
    MSG_TICKET_VIEW_HEADER,
)
from utils.formatters import format_datetime
from utils.helpers import build_ticket_service, extract_message_content

logger = structlog.get_logger()
router = Router()

MESSAGES_PER_PAGE = 10


def _format_messages(messages: list) -> str:
    """Format a list of message dicts into a readable conversation."""
    if not messages:
        return MSG_TICKET_NO_MESSAGES

    lines = []
    for msg in messages:
        sender = MSG_TICKET_SENDER_USER if msg["sender"] == "user" else MSG_TICKET_SENDER_SUPPORT
        ts = format_datetime(msg.get("timestamp", ""))

        content_parts = []
        if msg.get("text"):
            content_parts.append(msg["text"])
        if msg.get("file_id"):
            ft = msg.get("file_type", MSG_TICKET_FILE_LABEL)
            content_parts.append(f"[📎 {ft}]")

        content = " ".join(content_parts) if content_parts else f"[{MSG_TICKET_EMPTY_MESSAGE}]"
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
        MSG_TICKET_SUPPORT_HUB,
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
        MSG_TICKET_NEW_PROMPT,
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
    text, file_id, file_type = extract_message_content(message)

    if not text and not file_id:
        await message.answer(MSG_TICKET_SEND_TEXT)
        return

    service = build_ticket_service(ticket_repo, bot)
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
        MSG_TICKET_CREATED.format(ticket_id),
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
        MSG_TICKET_CANCELLED,
        reply_markup=KeyboardFactory.support_menu(),
        parse_mode="HTML",
    )
    await callback.answer(MSG_TICKET_CANCEL_ANSWER)


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
    service = build_ticket_service(ticket_repo, bot)
    tickets = await service.get_user_active_tickets(callback.from_user.id)

    if not tickets:
        try:
            await callback.message.edit_text(
                MSG_TICKET_NO_OPEN,
                reply_markup=KeyboardFactory.support_menu(),
                parse_mode="HTML",
            )
        except TelegramBadRequest:
            pass  # message content unchanged — ignore
        await callback.answer()
        return

    await callback.message.edit_text(
        MSG_TICKET_OPEN_HEADER.format(len(tickets)),
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
    service = build_ticket_service(ticket_repo, bot)
    ticket = await service.get_ticket(callback_data.id)

    if not ticket:
        await callback.answer(MSG_TICKET_NOT_FOUND, show_alert=True)
        return

    # Store ticket_id in FSM data for pagination
    await state.update_data(viewing_ticket_id=callback_data.id)

    messages = await service.get_conversation_history(
        callback_data.id, page=0, page_size=MESSAGES_PER_PAGE
    )
    total = await service.get_message_count(callback_data.id)
    total_pages = max(1, math.ceil(total / MESSAGES_PER_PAGE))

    status_label = MSG_TICKET_STATUS_OPEN if ticket["status"] == "open" else MSG_TICKET_STATUS_CLOSED
    is_closed = ticket["status"] == "closed"

    header = (
        MSG_TICKET_VIEW_HEADER.format(callback_data.id, status_label) + "\n"
        f"{'─' * 28}\n\n"
    )
    body = _format_messages(messages)

    if total_pages > 1:
        footer = MSG_TICKET_PAGE_FOOTER.format(1, total_pages, total)
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
        await callback.answer(MSG_TICKET_ERROR_REOPEN, show_alert=True)
        return

    page = callback_data.page
    service = build_ticket_service(ticket_repo, bot)

    messages = await service.get_conversation_history(
        ticket_id, page=page, page_size=MESSAGES_PER_PAGE
    )
    total = await service.get_message_count(ticket_id)
    total_pages = max(1, math.ceil(total / MESSAGES_PER_PAGE))

    header = (
        MSG_TICKET_VIEW_HEADER.format(ticket_id, "") + "\n"
        f"{'─' * 28}\n\n"
    )
    body = _format_messages(messages)
    footer = MSG_TICKET_PAGE_FOOTER.format(page + 1, total_pages, total)

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
        MSG_TICKET_REPLY_PROMPT.format(callback_data.id),
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
        await message.answer(MSG_TICKET_REPLY_ERROR)
        return

    text, file_id, file_type = extract_message_content(message)

    if not text and not file_id:
        await message.answer(MSG_TICKET_SEND_REPLY)
        return

    service = build_ticket_service(ticket_repo, bot)
    success = await service.user_reply(
        ticket_id,
        text=text,
        file_id=file_id,
        file_type=file_type,
    )

    await state.clear()

    if success:
        await message.answer(
            MSG_TICKET_REPLY_SUCCESS.format(ticket_id),
            reply_markup=KeyboardFactory.support_menu(),
        )
    else:
        await message.answer(
            MSG_TICKET_CLOSED_OR_MISSING,
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
    service = build_ticket_service(ticket_repo, bot)
    success = await service.close_ticket(callback_data.id)

    if success:
        await callback.message.edit_text(
            MSG_TICKET_CLOSED_CONFIRM.format(callback_data.id),
            reply_markup=KeyboardFactory.support_menu(),
            parse_mode="HTML",
        )
    else:
        await callback.answer(MSG_TICKET_CLOSE_ERROR, show_alert=True)

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
    service = build_ticket_service(ticket_repo, bot)
    tickets = await service.get_user_closed_tickets(callback.from_user.id)

    if not tickets:
        try:
            await callback.message.edit_text(
                MSG_TICKET_NO_CLOSED,
                reply_markup=KeyboardFactory.support_menu(),
                parse_mode="HTML",
            )
        except TelegramBadRequest:
            pass
        await callback.answer()
        return

    try:
        await callback.message.edit_text(
            MSG_TICKET_CLOSED_HEADER.format(len(tickets)),
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
    service = build_ticket_service(ticket_repo, bot)
    success = await service.reopen_ticket(callback_data.id)

    if success:
        await callback.message.edit_text(
            MSG_TICKET_REOPENED.format(callback_data.id),
            reply_markup=KeyboardFactory.support_menu(),
            parse_mode="HTML",
        )
    else:
        await callback.answer(MSG_TICKET_REOPEN_ERROR, show_alert=True)

    await callback.answer()
