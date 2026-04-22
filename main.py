import asyncio
import logging
import sys

from aiohttp import web
from aiogram import Bot, Dispatcher, types
from datetime import datetime, timedelta

# Internal Project Imports
import sentry_sdk

from config import settings
from database.connection import init_db, mongo_client
from handlers.admin_routes import router as admin_router
from handlers.client_routes import router as client_router
from handlers.common import router as common_router
from middlewares.error_handler import GlobalErrorHandler
from middlewares.maintenance import MaintenanceMiddleware
from middlewares.throttling import ThrottlingMiddleware
from middlewares.db_injection import DbInjectionMiddleware
from middlewares.correlation import CorrelationLoggingMiddleware
from middlewares.activity_tracker import ActivityTrackerMiddleware
from utils.storage import MongoStorage

# Ensure console handles UTF-8 for emojis (especially on Windows)
if sys.stdout.encoding.lower() != "utf-8":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# ... imports
from utils.logger import setup_logger

# ... (imports)

# --- LOGGING CONFIGURATION ---
logger = setup_logger()

# --- SENTRY INITIALIZATION ---
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=0.1,  # Sample 10% of transactions for performance
        profiles_sample_rate=0.1,
    )
    logger.info("✅ Sentry Integration Enabled")
else:
    logger.warning("⚠️ Sentry DSN not found. Error tracking disabled.")


# --- BOT INITIALIZATION ---
bot = Bot(token=settings.BOT_TOKEN)

# Use MongoDB for persistent storage — must use the SAME DB as app data
storage = MongoStorage(mongo_client, db_name=settings.DB_NAME)
dp = Dispatcher(storage=storage)

# Register Middleware
# Order matters: Correlation -> Activity Tracker -> DB Injection -> Maintenance -> Throttling -> Error Handler
dp.message.outer_middleware(CorrelationLoggingMiddleware())
dp.callback_query.outer_middleware(CorrelationLoggingMiddleware())
dp.edited_message.outer_middleware(CorrelationLoggingMiddleware())
dp.message.outer_middleware(ActivityTrackerMiddleware())
dp.callback_query.outer_middleware(ActivityTrackerMiddleware())
dp.edited_message.outer_middleware(ActivityTrackerMiddleware())
dp.message.middleware(DbInjectionMiddleware())
dp.callback_query.middleware(DbInjectionMiddleware())
dp.edited_message.middleware(DbInjectionMiddleware())
dp.message.middleware(ThrottlingMiddleware(rate_limit=0.5))
dp.callback_query.middleware(ThrottlingMiddleware(rate_limit=0.5))
dp.message.middleware(MaintenanceMiddleware())
dp.message.middleware(GlobalErrorHandler())
dp.callback_query.middleware(GlobalErrorHandler())
dp.edited_message.middleware(GlobalErrorHandler())

# Register all hander routers
dp.include_router(common_router)
dp.include_router(client_router)
dp.include_router(admin_router)


# --- KEEP-ALIVE WEB SERVER FOR RAILWAY ---
async def handle_ping(request):
    return web.Response(text="Bot is running!")

async def start_keepalive_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    app.router.add_get("/health", handle_ping)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    import os
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info("Keep-alive server started", port=port)
    return runner


async def session_timeout_worker(bot: Bot, storage: MongoStorage):
    """
    Background worker that runs every minute to check for inactive FSM sessions.
    If a session has been inactive for 20 minutes and has an active state,
    it clears the state and notifies the user.
    """
    while True:
        try:
            now = datetime.utcnow()
            cutoff = now - timedelta(minutes=20)
            
            # Find users who have an active state but haven't interacted in 20 mins
            expired_docs = storage.collection.find({
                "last_activity": {"$lt": cutoff},
                "state": {"$ne": None}
            })
            
            async for doc in expired_docs:
                chat_id = doc.get("chat_id")
                user_id = doc.get("user_id")
                
                if chat_id and user_id:
                    # Notify user
                    msg = "⏳ عذراً، انتهت صلاحية الجلسة لعدم النشاط (20 دقيقة). تم إغلاق الجلسة السابقة وإعادة تعيين المحادثة."
                    try:
                        await bot.send_message(chat_id, msg)
                    except Exception as e:
                        logger.warning(f"Could not send timeout message to chat {chat_id}: {e}")
                    
                    # Clear state
                    await storage.collection.update_one(
                        {"_id": doc["_id"]},
                        {"$unset": {"state": "", "data": ""}}
                    )
        except Exception as e:
            logger.error("Error in session timeout worker", e=str(e), exc_info=True)
            
        await asyncio.sleep(60)


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
            types.BotCommand(command="admin", description="🛠 لوحة التحكم"),
            types.BotCommand(command="stats", description="📊 الإحصائيات"),
            types.BotCommand(command="maintenance_on", description="🛑 تفعيل الصيانة"),
            types.BotCommand(command="maintenance_off", description="✅ إيقاف الصيانة"),
        ]

        # Apply student commands to everyone
        await bot.set_my_commands(
            student_commands, scope=types.BotCommandScopeDefault()
        )

        # Apply admin commands only to admins
        for admin_id in settings.admin_ids:
            await bot.set_my_commands(
                admin_commands, scope=types.BotCommandScopeChat(chat_id=admin_id)
            )

        logger.info("Bot online", admin_ids=settings.admin_ids)

        await bot.delete_webhook(drop_pending_updates=True)
        
        # Start keep-alive web server for Railway
        runner = await start_keepalive_server()
        
        # Start session timeout background worker
        timeout_task = asyncio.create_task(session_timeout_worker(bot, storage))
        
        await dp.start_polling(bot)

    except Exception as e:
        logger.error("Error occurred while running bot", e=str(e), exc_info=True)
    finally:
        await bot.session.close()
        try:
            if 'runner' in locals() and runner:
                await runner.cleanup()
        except Exception:
            pass
        try:
            if 'timeout_task' in locals():
                timeout_task.cancel()
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())
