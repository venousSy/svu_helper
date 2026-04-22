from typing import Any, Awaitable, Callable, Dict
from datetime import datetime

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

from infrastructure.mongo_db import Database


class ActivityTrackerMiddleware(BaseMiddleware):
    """
    Updates the last_activity timestamp for the user in the FSM storage
    whenever they interact with the bot. This allows the session timeout
    worker to accurately determine inactivity.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # We only track activity for messages and callbacks
        chat_id = None
        user_id = None
        
        if isinstance(event, Message):
            chat_id = event.chat.id
            user_id = event.from_user.id if event.from_user else None
        elif isinstance(event, CallbackQuery):
            chat_id = event.message.chat.id if event.message else None
            user_id = event.from_user.id if event.from_user else None
            
        if chat_id and user_id:
            db = Database.db
            # We assume fsm_states is the default collection used by MongoStorage
            await db["fsm_states"].update_one(
                {"chat_id": chat_id, "user_id": user_id},
                {"$set": {"last_activity": datetime.utcnow()}},
                upsert=True
            )

        return await handler(event, data)
