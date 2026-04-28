"""
One-time migration script: Convert price field from string to int (SP).
Deletes any project with an unparseable price.

Run once from the project root:
    python scripts/migrate_prices.py
"""
import re
import sys
import os

# Load .env manually so we don't need the full app stack
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

import pymongo
import structlog

logger = structlog.get_logger(__name__)

MONGO_URI = os.environ["MONGO_URI"]
DB_NAME   = os.environ.get("DB_NAME", "svu_helper_bot")


def migrate_prices():
    logger.info("Connecting to MongoDB (synchronous pymongo)…", db=DB_NAME)
    client = pymongo.MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=30_000,
        tlsAllowInvalidCertificates=True,   # bypass Python 3.14 SSL quirks for this local script
    )
    
    # Ping to verify connection before doing any work
    try:
        client.admin.command("ping")
        logger.info("Connection OK ✅")
    except Exception as e:
        logger.error("Cannot reach MongoDB — check Atlas IP whitelist", error=str(e))
        sys.exit(1)

    db = client[DB_NAME]
    projects = db["projects"]

    migrated = 0
    deleted  = 0
    skipped  = 0

    for doc in projects.find({}):
        pid   = doc["_id"]
        price = doc.get("price")

        # Already a clean int — nothing to do
        if isinstance(price, int):
            skipped += 1
            continue

        # Float → int (e.g. 150.0 → 150)
        if isinstance(price, float):
            projects.update_one({"_id": pid}, {"$set": {"price": int(price)}})
            migrated += 1
            logger.info("float→int", project_id=str(pid), old=price, new=int(price))
            continue

        # String → extract digits
        if isinstance(price, str):
            digits = re.sub(r"[^\d]", "", price)
            if digits:
                new_price = int(digits)
                projects.update_one({"_id": pid}, {"$set": {"price": new_price}})
                migrated += 1
                logger.info("str→int", project_id=str(pid), old=price, new=new_price)
            else:
                projects.delete_one({"_id": pid})
                deleted += 1
                logger.warning("deleted (unparseable price)", project_id=str(pid), price=price)
            continue

        # None or unknown type — skip (price was never set, that's valid)
        if price is None:
            skipped += 1
            continue

        # Unknown type → delete
        projects.delete_one({"_id": pid})
        deleted += 1
        logger.warning("deleted (unknown price type)", project_id=str(pid), price_type=type(price).__name__)

    logger.info("Migration complete ✅", migrated=migrated, deleted=deleted, skipped=skipped)
    client.close()


if __name__ == "__main__":
    migrate_prices()
