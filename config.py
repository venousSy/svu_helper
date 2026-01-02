import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
# If ADMIN_ID is missing, it defaults to 0 to prevent a crash
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))