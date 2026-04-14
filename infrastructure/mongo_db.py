"""
Infrastructure – MongoDB Connection
=====================================
Manages the global MongoDB client and provides the `Database` class
for lifecycle management (connect, index creation, sequence counters).

Indexes created at startup
--------------------------
projects:
  - id          (unique)  – fast look-up by project ID
  - user_id               – filter projects per student
  - status                – filter by workflow state
  - created_at (desc)     – time-based sorting / stats

payments:
  - id          (unique)  – fast look-up by payment ID
  - project_id            – find payment for a project
  - status                – filter pending / accepted receipts
  - created_at (desc)     – time-based sorting / stats

This module is the single place that knows about Motor / Motor-asyncio.
Application and domain layers must never import from here directly;
instead, use the `get_db` helper or receive `db` via DI middleware.
"""
import structlog
from pymongo import DESCENDING

from motor.motor_asyncio import AsyncIOMotorClient

from config import settings

logger = structlog.get_logger()

DB_NAME = settings.DB_NAME

# Module-level client (lazy connection, one per process)
mongo_client = AsyncIOMotorClient(settings.MONGO_URI)


class Database:
    """Manages the Motor database handle and one-time setup tasks."""

    client: AsyncIOMotorClient = mongo_client
    db = None  # Set by connect()

    @classmethod
    async def connect(cls) -> None:
        """Initialises the MongoDB connection and ensures required indexes."""
        cls.db = cls.client[DB_NAME]
        logger.info("Connected to MongoDB", db_name=DB_NAME)

        # --- Index creation ---
        await cls.db.projects.create_index("id", unique=True)
        await cls.db.projects.create_index("user_id")
        await cls.db.projects.create_index("status")
        await cls.db.projects.create_index([("created_at", DESCENDING)])

        await cls.db.payments.create_index("id", unique=True)
        await cls.db.payments.create_index("project_id")
        await cls.db.payments.create_index("status")
        await cls.db.payments.create_index([("created_at", DESCENDING)])

        # FSM state storage — compound index for fast per-user look-ups
        await cls.db.fsm_states.create_index(
            [("chat_id", 1), ("user_id", 1)],
            unique=True,
        )

        # --- Ticket indexes ---
        await cls.db.tickets.create_index("ticket_id", unique=True)
        await cls.db.tickets.create_index(
            "message_thread_id", unique=True, sparse=True
        )
        await cls.db.tickets.create_index("user_id")
        await cls.db.tickets.create_index(
            [("user_id", 1), ("status", 1)]
        )

    @classmethod
    async def get_next_sequence(cls, sequence_name: str) -> int:
        """Atomically increments and returns the next integer ID."""
        if cls.db is None:
            await cls.connect()

        result = await cls.db.counters.find_one_and_update(
            {"_id": sequence_name},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=True,
        )
        return result["seq"]


async def get_db():
    """Returns the active database handle, connecting first if needed."""
    if Database.db is None:
        await Database.connect()
    return Database.db


async def init_db() -> None:
    """Public entry-point called at application startup."""
    await Database.connect()
