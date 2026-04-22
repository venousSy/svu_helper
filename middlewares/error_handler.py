import logging
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import TelegramObject, Message, CallbackQuery
import structlog

from utils.constants import MSG_GENERIC_ERROR, MSG_GENERIC_ERROR_SHORT

logger = structlog.get_logger()

class GlobalErrorHandler(BaseMiddleware):
    """
    Middleware to catch unhandled exceptions in handlers.
    Logs the error and sends a user-friendly message.
    """
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception as e:
            logger.exception("Uncaught exception processing update", dumped_event=str(event))
            
            # User Notification Logic
            # Check if we can reply to the user (Message or CallbackQuery)
            if isinstance(event, Message):
                try:
                    await event.answer(MSG_GENERIC_ERROR)
                except Exception:
                    pass # Only fails if we can't send messages (blocked etc)
            
            elif isinstance(event, CallbackQuery):
                try:
                    await event.answer(MSG_GENERIC_ERROR_SHORT, show_alert=True)
                except Exception:
                    pass
            
            # We explicitly return None to stop propagation if needed, 
            # though usually aiogram handles this.
            return None
