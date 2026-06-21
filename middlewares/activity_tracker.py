from typing import Any, Awaitable, Callable, Dict
from datetime import datetime, timezone

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import TelegramObject, Message, CallbackQuery


class ActivityTrackerMiddleware(BaseMiddleware):
    """
    Updates the last_activity timestamp for the user in the FSM storage
    whenever they interact with the bot. This allows the session timeout
    worker to accurately determine inactivity.

    NOTE: last_activity is stored inside the Redis-backed FSM data blob
    (via FSMContext.update_data), NOT in MongoDB. The FSM storage is Redis,
    so this is the only correct place to persist per-user activity timestamps.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Only track activity for messages and callbacks
        is_trackable = isinstance(event, (Message, CallbackQuery))

        if is_trackable:
            # aiogram injects the FSMContext (Redis-backed) into data["state"]
            state: FSMContext = data.get("state")
            if state is not None:
                await state.update_data(
                    last_activity=datetime.now(timezone.utc).isoformat()
                )

        return await handler(event, data)
