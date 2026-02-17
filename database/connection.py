
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from config import settings

# Use a default DB name if not specified in URI, or fall back to 'svu_helper_db'
DB_NAME = settings.DB_NAME

# Create a global client instance (lazy connection)
mongo_client = AsyncIOMotorClient(settings.MONGO_URI)

class Database:
    client: AsyncIOMotorClient = mongo_client
    db = None

    @classmethod
    async def connect(cls):
        """Initializes the MongoDB connection."""
        cls.db = cls.client[DB_NAME]
        logging.info(f"🔌 Connected to MongoDB: {DB_NAME}")

        # Ensure indexes
        # Projects
        await cls.db.projects.create_index("id", unique=True)
        await cls.db.projects.create_index("user_id")
        await cls.db.projects.create_index("status")

        # Payments
        await cls.db.payments.create_index("id", unique=True)
        await cls.db.payments.create_index("project_id")
        await cls.db.payments.create_index("status")
        
        # Sequence counters
        # (Implicitly handled by find_by_id on execution but good to be aware)

    @classmethod
    async def get_next_sequence(cls, sequence_name: str) -> int:
        """
        Atomically increments and returns the next integer ID for a sequence.
        """
        if cls.db is None:
            await cls.connect()
            
        result = await cls.db.counters.find_one_and_update(
            {"_id": sequence_name},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=True,
        )
        return result["seq"]

# Helper to ensure DB is connected
async def get_db():
    if Database.db is None:
        await Database.connect()
    return Database.db

# --- INITIALIZATION ---
async def init_db():
    """Wrapper to initialize the database connection."""
    await Database.connect()
