"""
Infrastructure – MongoDB Connection
=====================================
Manages the global MongoDB client and provides the `Database` class
for lifecycle management (connect, index creation, sequence counters).

This module is the single place that knows about Motor / Motor-asyncio.
Application and domain layers must never import from here directly;
instead, use the `get_db` helper or receive `db` via DI middleware.
"""
import logging

from motor.motor_asyncio import AsyncIOMotorClient

from config import settings

logger = logging.getLogger(__name__)

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
        logger.info(f"🔌 Connected to MongoDB: {DB_NAME}")

        # --- Index creation ---
        await cls.db.projects.create_index("id", unique=True)
        await cls.db.projects.create_index("user_id")
        await cls.db.projects.create_index("status")

        await cls.db.payments.create_index("id", unique=True)
        await cls.db.payments.create_index("project_id")
        await cls.db.payments.create_index("status")

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
