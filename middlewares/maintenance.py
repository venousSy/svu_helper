
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message

from config import settings
from utils.constants import MSG_MAINTENANCE_ACTIVE


class MaintenanceMiddleware(BaseMiddleware):
    """
    Blocks usage for non-admins when global maintenance mode is on.
    Reads settings_repo from the data dict injected by DbInjectionMiddleware.
    """

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        if event.from_user.id in settings.admin_ids:
            return await handler(event, data)

        settings_repo = data.get("settings_repo")
        if settings_repo and await settings_repo.get_maintenance_mode():
            await event.answer(
                MSG_MAINTENANCE_ACTIVE
            )
            return None

        return await handler(event, data)
