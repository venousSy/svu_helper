import logging
import os
import sys

from dotenv import load_dotenv

# Initialize logging for the config loader
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# --- BOT CONFIGURATION ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.critical("❌ BOT_TOKEN is missing in environment variables!")
    print("\nCRITICAL ERROR: BOT_TOKEN not found in .env file.")
    print("Please check your .env configuration.\n")
    sys.exit(1)

# Administrative IDs
try:
    # Try loading list first (ADMIN_IDS=123,456)
    env_ids = os.getenv("ADMIN_IDS", "")
    ADMIN_IDS = [int(x.strip()) for x in env_ids.split(",") if x.strip()]

    # Fallback/Support for single ADMIN_ID (or legacy variable acting as list)
    if not ADMIN_IDS:
        single_id = os.getenv("ADMIN_ID", "")
        # Check if user put a list in ADMIN_ID by mistake
        if "," in single_id:
            ADMIN_IDS = [int(x.strip()) for x in single_id.split(",") if x.strip()]
        elif single_id:
            ADMIN_IDS.append(int(single_id))

    if not ADMIN_IDS:
        raise ValueError("No valid admin IDs found in ADMIN_IDS or ADMIN_ID.")
        
except ValueError as e:
    logger.critical(f"❌ Invalid Admin Configuration: {e}")
    print("\nCRITICAL ERROR: ADMIN_IDS (comma-separated) or ADMIN_ID is required in .env file.")
    sys.exit(1)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

# --- FILE PATHS ---
# --- FILE PATHS ---
# DB_NAME removed as part of MongoDB migration
LOG_FILE = "bot.log"
