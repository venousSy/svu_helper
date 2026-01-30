"""
Database Management Module (MongoDB)
====================================
Handles all MongoDB operations using Motor (Async).
"""

import logging
from typing import Any, Dict, List, Optional, Union

from motor.motor_asyncio import AsyncIOMotorClient

from config import MONGO_URI
from utils.constants import (
    STATUS_ACCEPTED,
    STATUS_AWAITING_VERIFICATION,
    STATUS_DENIED_ADMIN,
    STATUS_DENIED_STUDENT,
    STATUS_FINISHED,
    STATUS_OFFERED,
    STATUS_PENDING,
    STATUS_REJECTED_PAYMENT,
)

# Use a default DB name if not specified in URI, or fall back to 'svu_helper_db'
DB_NAME = "svu_helper_bot"

if not MONGO_URI:
    raise ValueError("MONGO_URI is not set in environment or config.py")

# Create a global client instance (lazy connection)
mongo_client = AsyncIOMotorClient(MONGO_URI)

class Database:
    client: AsyncIOMotorClient = mongo_client
    db = None

    @classmethod
    async def connect(cls):
        """Initializes the MongoDB connection."""
        # Use simple topology check or just assign db
        cls.db = cls.client[DB_NAME]
        logging.info(f"🔌 Connected to MongoDB: {DB_NAME}")

        # Ensure indexes
        await cls.db.projects.create_index("id", unique=True)
        await cls.db.projects.create_index("user_id")
        await cls.db.projects.create_index("status")

        # Payment Indexes
        await cls.db.payments.create_index("id", unique=True)
        await cls.db.payments.create_index("project_id")
        await cls.db.payments.create_index("status")

    @classmethod
    async def get_next_sequence(cls, sequence_name: str) -> int:
        """
        Atomically increments and returns the next integer ID for a sequence.
        Used to maintain simple integer IDs for projects (like SQL AUTOINCREMENT).
        """
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


# --- PROJECT OPERATIONS ---


async def add_project(
    user_id: int,
    username: str,
    user_full_name: str,
    subject: str,
    tutor: str,
    deadline: str,
    details: str,
    file_id: Optional[str],
) -> int:
    db = await get_db()

    # Get next auto-increment ID
    project_id = await Database.get_next_sequence("project_id")

    document = {
        "id": project_id,
        "user_id": user_id,
        "username": username,
        "user_full_name": user_full_name,
        "subject_name": subject,
        "tutor_name": tutor,
        "deadline": deadline,
        "details": details,
        "file_id": file_id,
        "status": STATUS_PENDING,
        "price": None,
        "delivery_date": None,
    }

    await db.projects.insert_one(document)
    return project_id


async def get_pending_projects() -> List[Dict[str, Any]]:
    db = await get_db()
    cursor = db.projects.find({"status": STATUS_PENDING})
    return await cursor.to_list(length=None)


async def get_user_projects(user_id: int) -> List[Dict[str, Any]]:
    db = await get_db()
    cursor = db.projects.find({"user_id": user_id})
    return await cursor.to_list(length=None)


async def update_project_status(project_id: int, new_status: str) -> None:
    db = await get_db()
    await db.projects.update_one(
        {"id": int(project_id)}, {"$set": {"status": new_status}}
    )


async def get_all_projects_categorized() -> Dict[str, List[Dict[str, Any]]]:
    """Returns a dictionary of projects grouped by status."""
    db = await get_db()

    pending = await db.projects.find({"status": STATUS_PENDING}).to_list(length=None)

    ongoing = await db.projects.find(
        {"status": {"$in": [STATUS_ACCEPTED, STATUS_AWAITING_VERIFICATION]}}
    ).to_list(length=None)

    history = await db.projects.find(
        {
            "status": {
                "$in": [
                    STATUS_FINISHED,
                    STATUS_DENIED_ADMIN,
                    STATUS_DENIED_STUDENT,
                    STATUS_REJECTED_PAYMENT,
                ]
            }
        }
    ).to_list(length=None)

    offered = await db.projects.find({"status": STATUS_OFFERED}).to_list(length=None)

    return {
        "New / Pending": pending,
        "Offered / Waiting": offered,
        "Ongoing": ongoing,
        "History": history,
    }


async def get_all_users() -> List[int]:
    """Returns a list of unique user_ids."""
    db = await get_db()
    return await db.projects.distinct("user_id")


async def get_student_offers(user_id: int) -> List[Dict[str, Any]]:
    """Retrieves all projects for a user that currently have an active offer."""
    db = await get_db()
    cursor = db.projects.find({"user_id": user_id, "status": STATUS_OFFERED})
    return await cursor.to_list(length=None)


async def update_offer_details(proj_id: int, price: str, delivery: str) -> None:
    db = await get_db()
    await db.projects.update_one(
        {"id": int(proj_id)},
        {"$set": {"status": STATUS_OFFERED, "price": price, "delivery_date": delivery}},
    )


async def get_project_by_id(project_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves a single project by its integer ID."""
    db = await get_db()
    return await db.projects.find_one({"id": int(project_id)})


async def get_accepted_projects() -> List[Dict[str, Any]]:
    """Retrieves all active/ongoing projects."""
    db = await get_db()
    cursor = db.projects.find({"status": STATUS_ACCEPTED})
    return await cursor.to_list(length=None)


async def get_history_projects() -> List[Dict[str, Any]]:
    """Retrieves finished or denied projects."""
    db = await get_db()
    cursor = db.projects.find(
        {
            "status": {
                "$in": [
                    STATUS_FINISHED,
                    STATUS_DENIED_ADMIN,
                    STATUS_DENIED_STUDENT,
                    STATUS_REJECTED_PAYMENT,
                ]
            }
        }
    )
    return await cursor.to_list(length=None)


async def get_statistics() -> Dict[str, int]:
    """
    Aggregates project counts by status.
    Skipping revenue calculation as requested.
    """
    db = await get_db()
    
    # helper for counting
    async def count(query):
        return await db.projects.count_documents(query)
        
    stats = {
        "total": await count({}),
        "pending": await count({"status": STATUS_PENDING}),
        "active": await count({"status": {"$in": [STATUS_ACCEPTED, STATUS_AWAITING_VERIFICATION]}}),
        "finished": await count({"status": STATUS_FINISHED}),
        "denied": await count({"status": {"$in": [STATUS_DENIED_ADMIN, STATUS_DENIED_STUDENT]}})
    }
    return stats


# --- PAYMENT OPERATIONS ---


async def add_payment(project_id: int, user_id: int, file_id: str) -> int:
    db = await get_db()

    payment_id = await Database.get_next_sequence("payment_id")

    document = {
        "id": payment_id,
        "project_id": int(project_id),
        "user_id": user_id,
        "file_id": file_id,
        "status": "pending",  # pending, accepted, rejected
    }

    await db.payments.insert_one(document)
    return payment_id


async def get_payment_by_id(payment_id: int) -> Optional[Dict[str, Any]]:
    db = await get_db()
    return await db.payments.find_one({"id": int(payment_id)})


async def update_payment_status(payment_id: int, new_status: str) -> None:
    db = await get_db()
    await db.payments.update_one(
        {"id": int(payment_id)}, {"$set": {"status": new_status}}
    )


async def get_all_payments() -> List[Dict[str, Any]]:
    """Retrieves all payments sorted by ID descending (newest first)."""
    db = await get_db()
    cursor = db.payments.find().sort("id", -1)
    return await cursor.to_list(length=None)
