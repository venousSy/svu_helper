"""
Admin Ticket Handlers
=====================
Listens for admin replies inside Forum Topics and routes them to the
student who owns the ticket.

Filtering strategy
------------------
``F.message_thread_id`` ensures we only capture messages sent in a
topic thread (not general chat).  We then look up the ticket by
``message_thread_id`` — if no match, the message is silently ignored
(it belongs to a non-ticket topic).
"""
from typing import Optional

from aiogram import Bot, F, Router, types

import structlog

from config import settings
from infrastructure.repositories.ticket import TicketRepository
from utils.helpers import build_ticket_service, extract_message_content

logger = structlog.get_logger()
router = Router()





def _get_forum_group_id() -> Optional[int]:
    return getattr(settings, "ADMIN_FORUM_GROUP_ID", None)


# ------------------------------------------------------------------
# Admin reply in Forum Topic
# ------------------------------------------------------------------
@router.message(
    F.message_thread_id,
    F.chat.type.in_({"group", "supergroup"}),
)
async def admin_forum_reply(
    message: types.Message,
    ticket_repo: TicketRepository,
    bot: Bot,
):
    """Catch admin messages in Forum Topics and forward to the student.

    This handler fires for ANY threaded message in ANY supergroup the
    bot sees.  We filter on two conditions:
      1. The chat must be the configured Forum Group.
      2. The thread must map to an existing ticket in the DB.
    If either condition fails we silently return so other handlers
    (or other bots) can process the message.
    """
    forum_group_id = _get_forum_group_id()
    if not forum_group_id:
        return  # Ticket system not configured

    if message.chat.id != forum_group_id:
        return  # Not our forum group

    # Ignore bot's own messages
    if message.from_user and message.from_user.is_bot:
        return

    service = build_ticket_service(ticket_repo, bot)

    text, file_id, file_type = extract_message_content(message)

    if not text and not file_id:
        return  # Empty message (sticker, etc.) — ignore

    ticket = await service.admin_reply(
        message.message_thread_id,
        text=text,
        file_id=file_id,
        file_type=file_type,
    )

    if ticket is None:
        # No ticket maps to this thread — not a ticket topic
        return

    if ticket["status"] == "closed":
        # The service already notified the admin in the topic
        return

    logger.info(
        "Admin reply forwarded to user",
        ticket_id=ticket["ticket_id"],
        user_id=ticket["user_id"],
        admin_id=message.from_user.id if message.from_user else None,
    )
