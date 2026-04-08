import time
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message
import cachetools

class ThrottlingMiddleware(BaseMiddleware):
    """
    Simple anti-spam middleware.
    Limits users to one request every `rate_limit` seconds.
    """

    def __init__(self, rate_limit: float = 2.0):
        self.rate_limit = rate_limit
        self.last_seen = cachetools.TTLCache(maxsize=10000, ttl=rate_limit)

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        from aiogram.types import CallbackQuery

        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
        else:
            return await handler(event, data)
        
        # Check if user is spamming
        if user_id in self.last_seen:
            # Drop the update (don't process it)
            return None 

        # Update last seen time and proceed
        self.last_seen[user_id] = time.time()
        return await handler(event, data)
