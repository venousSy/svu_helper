
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message

from config import ADMIN_IDS
from database import get_maintenance_mode

class MaintenanceMiddleware(BaseMiddleware):
    """
    Blocks usage for non-admins when global maintenance mode is on.
    """

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        # Only check Messages
        if not isinstance(event, Message):
            return await handler(event, data)

        # Allow admins to bypass
        if event.from_user.id in ADMIN_IDS:
            return await handler(event, data)

        # Check DB status
        if await get_maintenance_mode():
            await event.answer("⚠️ **النظام تحت الصيانة حالياً.**\nالرجاء المحاولة لاحقاً.")
            return None # Stop processing

        return await handler(event, data)
