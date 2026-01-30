import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage

# Internal Project Imports
from config import ADMIN_ID, BOT_TOKEN, LOG_FILE
from database import init_db
from handlers.admin import router as admin_router
from handlers.client import router as client_router
from handlers.common import router as common_router

# Ensure console handles UTF-8 for emojis (especially on Windows)
if sys.stdout.encoding.lower() != "utf-8":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# --- LOGGING CONFIGURATION ---
# Configure formatting for both console and file logs
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    handlers=[
        logging.StreamHandler(sys.stdout),  # Console output
        logging.FileHandler(LOG_FILE, encoding="utf-8"),  # Persistent file log
    ],
)
logger = logging.getLogger(__name__)

# --- BOT INITIALIZATION ---
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Register all hander routers
dp.include_router(common_router)
dp.include_router(client_router)
dp.include_router(admin_router)


# --- MAIN ENTRY POINT ---
async def main():
    """
    Initializes the bot, sets up commands, and starts the polling loop.
    Ensures the database is ready before accepting any updates.
    """
    try:
        # Step 1: Initialize Database schema
        await init_db()
        logger.info("📂 Database initialized.")

        # Set bot commands
        student_commands = [
            types.BotCommand(command="start", description="🏠 القائمة الرئيسية"),
            types.BotCommand(command="new_project", description="📚 تقديم مشروع جديد"),
            types.BotCommand(command="my_projects", description="📂 عرض مشاريعي"),
            types.BotCommand(command="my_offers", description="🎁 الأسعار والعروض"),
            types.BotCommand(command="help", description="❓ مساعدة"),
            types.BotCommand(command="cancel", description="🚫 إلغاء العملية"),
        ]

        admin_commands = [
            types.BotCommand(command="admin", description="🛠 لوحة التحكم")
        ]

        # Apply student commands to everyone
        await bot.set_my_commands(
            student_commands, scope=types.BotCommandScopeDefault()
        )

        # Apply admin commands only to admin
        await bot.set_my_commands(
            admin_commands, scope=types.BotCommandScopeChat(chat_id=ADMIN_ID)
        )

        logger.info(f"🚀 Bot online. Admin ID: {ADMIN_ID}")

        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)

    except Exception as e:
        logger.error(f"⚠️ Error: {e}", exc_info=True)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
