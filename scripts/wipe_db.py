import asyncio
import os

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient


async def wipe_database():
    load_dotenv()
    mongo_uri = os.getenv("MONGO_URI")
    db_name = "svu_helper_bot"

    if not mongo_uri:
        print("❌ MONGO_URI not found in .env")
        return

    print(f"🔄 Connecting to {db_name}...")
    client = AsyncIOMotorClient(mongo_uri)
    db = client[db_name]

    # List collections to drop
    collections = ["projects", "payments", "counters"]

    for coll in collections:
        print(f"🗑 Dropping collection: {coll}")
        await db[coll].drop()

    print("✅ Database wiped successfully!")


if __name__ == "__main__":
    asyncio.run(wipe_database())
