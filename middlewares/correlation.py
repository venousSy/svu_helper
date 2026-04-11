import time
import uuid
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
import structlog

logger = structlog.get_logger()

class CorrelationLoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Clear previous context variables if any
        structlog.contextvars.clear_contextvars()

        correlation_id = str(uuid.uuid4())
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)

        # Extract useful data for logging securely
        user_id = None
        event_type = type(event).__name__
        
        if isinstance(event, Message) and event.from_user:
            user_id = event.from_user.id
            structlog.contextvars.bind_contextvars(user_id=user_id, chat_id=event.chat.id, message_id=event.message_id)
            logger.info("Incoming message", text_length=len(event.text) if event.text else 0)
        elif isinstance(event, CallbackQuery) and event.from_user:
            user_id = event.from_user.id
            structlog.contextvars.bind_contextvars(user_id=user_id, callback_data=event.data)
            logger.info("Incoming callback query")
        else:
            logger.info("Incoming update", event_type=event_type)

        start_time = time.perf_counter()
        
        try:
            return await handler(event, data)
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.info("Update processed", duration_ms=round(duration_ms, 2))
            structlog.contextvars.clear_contextvars()
