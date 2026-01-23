import os
import sys
import logging
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

# Administrative ID
try:
    ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
    if ADMIN_ID == 0:
        raise ValueError("ADMIN_ID cannot be 0")
except ValueError as e:
    logger.critical(f"❌ Invalid or missing ADMIN_ID: {e}")
    print("\nCRITICAL ERROR: ADMIN_ID is required in .env file.")
    sys.exit(1)

MONGO_URI = os.getenv("MONGO_URI")

# --- FILE PATHS ---
# --- FILE PATHS ---
# DB_NAME removed as part of MongoDB migration
LOG_FILE = "bot.log"
