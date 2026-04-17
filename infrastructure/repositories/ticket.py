"""
Ticket Repository
=================
Data-access layer for the ``tickets`` collection.

All MongoDB operations are async via Motor.  Handlers never call this
directly – they receive ``ticket_repo`` via the DI middleware.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog

from domain.entities import Ticket, TicketMessage
from domain.enums import TicketStatus
from infrastructure.mongo_db import Database

logger = structlog.get_logger()

DEFAULT_MSG_PAGE_SIZE: int = 10
MAX_MSG_PAGE_SIZE: int = 50


class TicketRepository:
    def __init__(self, db) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------
    async def create_ticket(
        self,
        *,
        user_id: int,
        initial_text: Optional[str] = None,
        file_id: Optional[str] = None,
        file_type: Optional[str] = None,
    ) -> int:
        """Insert a new ticket with an optional first message."""
        ticket_id = await Database.get_next_sequence("ticket_id")

        first_message = TicketMessage(
            sender="user",
            text=initial_text,
            file_id=file_id,
            file_type=file_type,
        )

        ticket = Ticket(
            ticket_id=ticket_id,
            user_id=user_id,
            messages=[first_message],
        )

        # exclude_none=True ensures fields like message_thread_id are
        # ABSENT (not null) in MongoDB, which is required for the
        # sparse unique index to allow multiple tickets without a topic.
        await self._db.tickets.insert_one(
            ticket.model_dump(exclude_none=True)
        )
        logger.info(
            "Ticket created", ticket_id=ticket_id, user_id=user_id
        )
        return ticket_id

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------
    async def get_ticket_by_id(
        self, ticket_id: int
    ) -> Optional[Dict[str, Any]]:
        return await self._db.tickets.find_one({"ticket_id": ticket_id})

    async def get_ticket_by_thread(
        self, message_thread_id: int
    ) -> Optional[Dict[str, Any]]:
        """Look up a ticket by its Forum Topic thread ID."""
        return await self._db.tickets.find_one(
            {"message_thread_id": message_thread_id}
        )

    async def get_active_tickets(
        self, user_id: int
    ) -> List[Dict[str, Any]]:
        """Return all open tickets for a user (compound index hit)."""
        cursor = (
            self._db.tickets.find(
                {"user_id": user_id, "status": TicketStatus.OPEN}
            )
            .sort("ticket_id", -1)
        )
        return await cursor.to_list(length=100)

    async def get_recent_messages(
        self,
        ticket_id: int,
        *,
        page: int = 0,
        page_size: int = DEFAULT_MSG_PAGE_SIZE,
    ) -> List[Dict[str, Any]]:
        """Return a page of messages for a ticket (newest first).

        Uses MongoDB ``$slice`` projection to implement server-side
        pagination over the embedded ``messages`` array.
        """
        page_size = min(page_size, MAX_MSG_PAGE_SIZE)
        skip = page * page_size

        # $slice with [negative_skip, limit] gives the *last* N entries
        # after skipping from the end.  We want newest-first pages.
        doc = await self._db.tickets.find_one(
            {"ticket_id": ticket_id},
            {"messages": 1, "_id": 0},
        )
        if not doc or "messages" not in doc:
            return []

        messages = doc["messages"]
        total = len(messages)

        # Newest first, paginated
        start = max(total - skip - page_size, 0)
        end = total - skip
        page_msgs = messages[start:end]
        page_msgs.reverse()  # newest first
        return page_msgs

    async def get_message_count(self, ticket_id: int) -> int:
        """Return the total number of messages in a ticket."""
        doc = await self._db.tickets.find_one(
            {"ticket_id": ticket_id},
            {"messages": 1, "_id": 0},
        )
        if not doc or "messages" not in doc:
            return 0
        return len(doc["messages"])

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------
    async def set_thread_id(
        self, ticket_id: int, message_thread_id: int
    ) -> None:
        """Link a ticket to a Telegram Forum Topic."""
        await self._db.tickets.update_one(
            {"ticket_id": ticket_id},
            {"$set": {"message_thread_id": message_thread_id}},
        )
        logger.info(
            "Ticket linked to forum topic",
            ticket_id=ticket_id,
            thread_id=message_thread_id,
        )

    async def add_message(
        self,
        ticket_id: int,
        *,
        sender: str,
        text: Optional[str] = None,
        file_id: Optional[str] = None,
        file_type: Optional[str] = None,
    ) -> None:
        """Append a message to the ticket's conversation history."""
        msg = TicketMessage(
            sender=sender,
            text=text,
            file_id=file_id,
            file_type=file_type,
        )
        await self._db.tickets.update_one(
            {"ticket_id": ticket_id},
            {"$push": {"messages": msg.model_dump()}},
        )
        logger.debug(
            "Message added to ticket",
            ticket_id=ticket_id,
            sender=sender,
        )

    async def close_ticket(self, ticket_id: int) -> None:
        """Mark a ticket as closed."""
        await self._db.tickets.update_one(
            {"ticket_id": ticket_id},
            {"$set": {"status": TicketStatus.CLOSED}},
        )
        logger.info("Ticket closed", ticket_id=ticket_id)

    async def reopen_ticket(self, ticket_id: int) -> None:
        """Mark a closed ticket as open again."""
        await self._db.tickets.update_one(
            {"ticket_id": ticket_id},
            {"$set": {"status": TicketStatus.OPEN}},
        )
        logger.info("Ticket reopened", ticket_id=ticket_id)

    # ------------------------------------------------------------------
    # Read (closed)
    # ------------------------------------------------------------------
    async def get_closed_tickets(
        self, user_id: int
    ) -> List[Dict[str, Any]]:
        """Return all closed tickets for a user."""
        cursor = (
            self._db.tickets.find(
                {"user_id": user_id, "status": TicketStatus.CLOSED}
            )
            .sort("ticket_id", -1)
        )
        return await cursor.to_list(length=100)
