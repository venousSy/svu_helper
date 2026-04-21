"""
Ticket Service
==============
Orchestration layer that combines TicketRepository data access with
Telegram Bot API calls (forum topic management, message forwarding).

Handlers call this service instead of touching the repo + bot directly,
keeping handler code thin and testable.
"""
from typing import Any, Dict, List, Optional

import structlog
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from infrastructure.repositories.ticket import TicketRepository

logger = structlog.get_logger()


class TicketService:
    """High-level operations for the support ticket workflow."""

    def __init__(
        self,
        ticket_repo: TicketRepository,
        bot: Bot,
        forum_group_id: Optional[int],
    ) -> None:
        self._repo = ticket_repo
        self._bot = bot
        self._forum_group_id = forum_group_id

    # ------------------------------------------------------------------
    # Open a new ticket
    # ------------------------------------------------------------------
    async def open_ticket(
        self,
        *,
        user_id: int,
        username: Optional[str] = None,
        user_full_name: Optional[str] = None,
        text: Optional[str] = None,
        file_id: Optional[str] = None,
        file_type: Optional[str] = None,
    ) -> int:
        """Create a ticket, open a Forum Topic, and post the first msg."""
        ticket_id = await self._repo.create_ticket(
            user_id=user_id,
            username=username,
            user_full_name=user_full_name,
            initial_text=text,
            file_id=file_id,
            file_type=file_type,
        )

        # Attempt to create a Forum Topic in the admin group
        if self._forum_group_id:
            thread_id = await self._create_forum_topic(ticket_id, user_id)
            if thread_id:
                await self._repo.set_thread_id(ticket_id, thread_id)
                await self._send_to_topic(
                    thread_id, text, file_id, file_type,
                    header=f"🎫 تذكرة جديدة #{ticket_id}\n👤 المستخدم: {user_id}",
                )

        return ticket_id

    # ------------------------------------------------------------------
    # User replies to an existing ticket
    # ------------------------------------------------------------------
    async def user_reply(
        self,
        ticket_id: int,
        *,
        text: Optional[str] = None,
        file_id: Optional[str] = None,
        file_type: Optional[str] = None,
    ) -> bool:
        """Save the user's reply and forward it to the admin topic."""
        ticket = await self._repo.get_ticket_by_id(ticket_id)
        if not ticket:
            return False

        await self._repo.add_message(
            ticket_id,
            sender="user",
            text=text,
            file_id=file_id,
            file_type=file_type,
        )

        thread_id = ticket.get("message_thread_id")
        if thread_id and self._forum_group_id:
            await self._send_to_topic(
                thread_id, text, file_id, file_type,
                header="💬 رد من الطالب:",
            )

        return True

    # ------------------------------------------------------------------
    # Admin replies from the Forum Topic
    # ------------------------------------------------------------------
    async def admin_reply(
        self,
        message_thread_id: int,
        *,
        text: Optional[str] = None,
        file_id: Optional[str] = None,
        file_type: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Save admin reply in DB and forward to the user.

        Returns the ticket dict or None if no matching ticket.
        """
        ticket = await self._repo.get_ticket_by_thread(message_thread_id)
        if not ticket:
            return None

        if ticket["status"] == "closed":
            # Inform the admin the ticket is closed
            if self._forum_group_id:
                try:
                    await self._bot.send_message(
                        chat_id=self._forum_group_id,
                        message_thread_id=message_thread_id,
                        text="⚠️ هذه التذكرة مغلقة. لا يمكن إرسال ردود.",
                    )
                except Exception:
                    pass
            return ticket

        await self._repo.add_message(
            ticket["ticket_id"],
            sender="admin",
            text=text,
            file_id=file_id,
            file_type=file_type,
        )

        # Forward the reply to the student
        user_id = ticket["user_id"]
        header = f"📩 رد من الدعم الفني (تذكرة #{ticket['ticket_id']}):"
        await self._send_to_user(user_id, text, file_id, file_type, header=header)

        return ticket

    # ------------------------------------------------------------------
    # Close a ticket
    # ------------------------------------------------------------------
    async def close_ticket(self, ticket_id: int) -> bool:
        """Close a ticket and optionally close the Forum Topic."""
        ticket = await self._repo.get_ticket_by_id(ticket_id)
        if not ticket:
            return False

        await self._repo.close_ticket(ticket_id)

        thread_id = ticket.get("message_thread_id")
        if thread_id and self._forum_group_id:
            try:
                await self._bot.close_forum_topic(
                    chat_id=self._forum_group_id,
                    message_thread_id=thread_id,
                )
            except TelegramBadRequest as e:
                logger.warning(
                    "Could not close forum topic",
                    thread_id=thread_id,
                    error=str(e),
                )
            except Exception as e:
                logger.error(
                    "Unexpected error closing forum topic",
                    thread_id=thread_id,
                    error=str(e),
                )

        return True

    # ------------------------------------------------------------------
    # Read helpers
    # ------------------------------------------------------------------
    async def get_user_active_tickets(
        self, user_id: int
    ) -> List[Dict[str, Any]]:
        return await self._repo.get_active_tickets(user_id)

    async def get_all_active_tickets(
        self, page: int = 0, page_size: int = 5
    ) -> tuple[List[Dict[str, Any]], int]:
        return await self._repo.get_all_active_tickets(page, page_size)

    async def get_user_closed_tickets(
        self, user_id: int
    ) -> List[Dict[str, Any]]:
        return await self._repo.get_closed_tickets(user_id)

    async def get_conversation_history(
        self,
        ticket_id: int,
        *,
        page: int = 0,
        page_size: int = 10,
    ) -> List[Dict[str, Any]]:
        return await self._repo.get_recent_messages(
            ticket_id, page=page, page_size=page_size
        )

    async def get_message_count(self, ticket_id: int) -> int:
        return await self._repo.get_message_count(ticket_id)

    async def get_ticket(self, ticket_id: int) -> Optional[Dict[str, Any]]:
        return await self._repo.get_ticket_by_id(ticket_id)

    # ------------------------------------------------------------------
    # Reopen a closed ticket
    # ------------------------------------------------------------------
    async def reopen_ticket(self, ticket_id: int) -> bool:
        """Reopen a closed ticket and optionally reopen the Forum Topic."""
        ticket = await self._repo.get_ticket_by_id(ticket_id)
        if not ticket:
            return False

        await self._repo.reopen_ticket(ticket_id)

        thread_id = ticket.get("message_thread_id")
        if thread_id and self._forum_group_id:
            try:
                await self._bot.reopen_forum_topic(
                    chat_id=self._forum_group_id,
                    message_thread_id=thread_id,
                )
            except TelegramBadRequest as e:
                logger.warning(
                    "Could not reopen forum topic",
                    thread_id=thread_id,
                    error=str(e),
                )
            except Exception as e:
                logger.error(
                    "Unexpected error reopening forum topic",
                    thread_id=thread_id,
                    error=str(e),
                )

        return True

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
    async def _create_forum_topic(
        self, ticket_id: int, user_id: int
    ) -> Optional[int]:
        """Create a Forum Topic and return its thread ID."""
        try:
            topic = await self._bot.create_forum_topic(
                chat_id=self._forum_group_id,
                name=f"🎫 تذكرة #{ticket_id} — {user_id}",
            )
            logger.info(
                "Forum topic created",
                ticket_id=ticket_id,
                thread_id=topic.message_thread_id,
            )
            return topic.message_thread_id
        except TelegramBadRequest as e:
            logger.error(
                "Failed to create forum topic — check bot admin rights",
                ticket_id=ticket_id,
                error=str(e),
            )
            return None
        except TelegramForbiddenError as e:
            logger.error(
                "Bot is not a member of the forum group",
                error=str(e),
            )
            return None

    async def _send_to_topic(
        self,
        thread_id: int,
        text: Optional[str],
        file_id: Optional[str],
        file_type: Optional[str],
        *,
        header: str = "",
    ) -> None:
        """Send a message (text or file) into a Forum Topic."""
        if not self._forum_group_id:
            return
        try:
            await self._dispatch_message(
                chat_id=self._forum_group_id,
                text=text,
                file_id=file_id,
                file_type=file_type,
                header=header,
                message_thread_id=thread_id,
            )
        except Exception as e:
            logger.error(
                "Failed to send to forum topic",
                thread_id=thread_id,
                error=str(e),
            )

    async def _send_to_user(
        self,
        user_id: int,
        text: Optional[str],
        file_id: Optional[str],
        file_type: Optional[str],
        *,
        header: str = "",
    ) -> None:
        """Forward a message to the student's private chat."""
        try:
            await self._dispatch_message(
                chat_id=user_id,
                text=text,
                file_id=file_id,
                file_type=file_type,
                header=header,
            )
        except TelegramForbiddenError:
            logger.warning("User blocked the bot", user_id=user_id)
        except Exception as e:
            logger.error(
                "Failed to send to user",
                user_id=user_id,
                error=str(e),
            )

    async def _dispatch_message(
        self,
        *,
        chat_id: int,
        text: Optional[str],
        file_id: Optional[str],
        file_type: Optional[str],
        header: str = "",
        message_thread_id: Optional[int] = None,
    ) -> None:
        """Route the message to the correct Telegram send method."""
        kwargs: Dict[str, Any] = {"chat_id": chat_id}
        if message_thread_id:
            kwargs["message_thread_id"] = message_thread_id

        full_text = f"{header}\n\n{text}" if text else header

        if file_id and file_type == "photo":
            await self._bot.send_photo(
                **kwargs, photo=file_id, caption=full_text or None
            )
        elif file_id and file_type == "document":
            await self._bot.send_document(
                **kwargs, document=file_id, caption=full_text or None
            )
        elif file_id and file_type == "video":
            await self._bot.send_video(
                **kwargs, video=file_id, caption=full_text or None
            )
        elif file_id:
            # Unknown file type — send as document
            await self._bot.send_document(
                **kwargs, document=file_id, caption=full_text or None
            )
        else:
            await self._bot.send_message(**kwargs, text=full_text)
