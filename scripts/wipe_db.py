"""
wipe_db.py — Destructive maintenance script
============================================
Drops the core collections from the bot's MongoDB database.

⚠️  THIS IS IRREVERSIBLE.  Always take a backup first.

Usage::

    python scripts/wipe_db.py

The script will:
1. Print the target database and collections.
2. Ask for explicit confirmation by typing "WIPE".
3. Only proceed if the confirmation matches exactly.
"""
import asyncio
import sys

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from config import settings


# Collections that will be dropped.  Extend this list if new ones are added.
COLLECTIONS_TO_DROP = ["projects", "payments", "counters"]


async def wipe_database() -> None:
    db_name = settings.DB_NAME
    mongo_uri = settings.MONGO_URI  # read via pydantic-settings, not os.getenv

    print("=" * 55)
    print("⚠️   DATABASE WIPE UTILITY")
    print("=" * 55)
    print(f"  Target database : {db_name}")
    print(f"  Collections     : {', '.join(COLLECTIONS_TO_DROP)}")
    print("=" * 55)
    print()
    print("This operation is IRREVERSIBLE and will permanently")
    print("delete all data in the listed collections.")
    print()

    try:
        confirmation = input('Type  WIPE  to confirm, or anything else to abort: ').strip()
    except (EOFError, KeyboardInterrupt):
        print("\n❌ Aborted.")
        sys.exit(1)

    if confirmation != "WIPE":
        print("❌ Confirmation did not match.  Aborting — no data was deleted.")
        sys.exit(1)

    print()
    print(f"🔄 Connecting to {db_name}…")
    client = AsyncIOMotorClient(mongo_uri)
    db = client[db_name]

    for coll in COLLECTIONS_TO_DROP:
        print(f"   🗑  Dropping collection: {coll}")
        await db[coll].drop()

    client.close()
    print()
    print("✅ Database wiped successfully.")


if __name__ == "__main__":
    load_dotenv()
    asyncio.run(wipe_database())
