# main.py
import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN, ADMIN_ID
from handlers import client, admin, common  # Import the modules
from database import init_db
async def main():
    init_db() 
    print("✅ Database initialized successfully.")
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # The order matters: Admin filters usually go first 
    # so they don't get caught by broad client filters.
    dp.include_router(admin.router)
    dp.include_router(common.router)
    dp.include_router(client.router)

    print("🚀 Bot is running in MODULAR mode.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())