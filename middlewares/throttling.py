
import time
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message

class ThrottlingMiddleware(BaseMiddleware):
    """
    Simple anti-spam middleware.
    Limits users to one request every `rate_limit` seconds.
    """

    def __init__(self, rate_limit: float = 2.0):
        self.rate_limit = rate_limit
        self.last_seen: Dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        # Only throttle Message events (not callbacks, usually)
        if not isinstance(event, Message):
            return await handler(event, data)

        user_id = event.from_user.id
        current_time = time.time()
        
        last_time = self.last_seen.get(user_id, 0)
        
        # Check if user is spamming
        if current_time - last_time < self.rate_limit:
            # Drop the update (don't process it)
            # Optional: Send a warning (careful not to create an infinite loop of warnings)
            return None 

        # Update last seen time and proceed
        self.last_seen[user_id] = current_time
        return await handler(event, data)
