import asyncio
import os
import logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage

# Import your routers
from handlers.common import router as common_router
from handlers.client import router as client_router
from handlers.admin import router as admin_router

# --- CONFIGURATION ---
load_dotenv()
API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Include all routers
dp.include_router(common_router)
dp.include_router(client_router)
dp.include_router(admin_router)

# --- MAIN ---
async def main():
    try:
        # Set bot commands
        student_commands = [
            types.BotCommand(command="start", description="🏠 Main Menu"),
            types.BotCommand(command="new_project", description="📚 Submit New Project"),
            types.BotCommand(command="my_projects", description="📂 My Status"),
            types.BotCommand(command="my_offers", description="🎁 View My Offers"),
            types.BotCommand(command="help", description="❓ Help"),
            types.BotCommand(command="cancel", description="🚫 Cancel Process")
        ]
        
        admin_commands = student_commands + [
            types.BotCommand(command="admin", description="🛠 Admin Panel")
        ]
        
        # Apply student commands to everyone
        await bot.set_my_commands(student_commands, scope=types.BotCommandScopeDefault())
        
        # Apply admin commands only to admin
        await bot.set_my_commands(
            admin_commands, 
            scope=types.BotCommandScopeChat(chat_id=ADMIN_ID)
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