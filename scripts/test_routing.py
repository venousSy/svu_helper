import asyncio
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from aiogram import Bot, Dispatcher
from aiogram.types import Update, CallbackQuery, User, Chat, Message
from handlers.client_routes import router as client_router
from middlewares.db_injection import DbInjectionMiddleware
from config import settings

async def main():
    dp = Dispatcher()
    from handlers.common import router as common_router
    dp.include_router(common_router)
    dp.include_router(client_router)

    dp.update.middleware(DbInjectionMiddleware())
    
    bot = Bot(token="123456789:AABBCCDDEEFF")
    
    callbacks_to_test = [
        "team:find:0:",
        "menu:cancel_flow"
    ]

    
    for cb_data in callbacks_to_test:
        user = User(id=123, is_bot=False, first_name="Test")
        chat = Chat(id=123, type="private")
        msg = Message(message_id=1, date=0, chat=chat)
        cb = CallbackQuery(
            id="query_1",
            from_user=user,
            chat_instance="1",
            message=msg,
            data=cb_data
        )
        update = Update(update_id=1, callback_query=cb)
        
        try:
            handled = await dp.feed_update(bot, update)
            print(f"Update {cb_data} handled: {handled}")
        except Exception as e:
            print(f"Update {cb_data} failed with exception: {e}")

if __name__ == "__main__":
    asyncio.run(main())
