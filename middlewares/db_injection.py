"""
DB Injection Middleware
=======================
Builds repository instances for every incoming update and injects them
into the aiogram handler data dict.

Handlers declare typed parameters matching the keys below and aiogram
automatically resolves them:

    async def my_handler(
        message: types.Message,
        project_repo: ProjectRepository,
        payment_repo: PaymentRepository,
    ):
        ...

Design notes:
  - Repositories are lightweight objects (just a reference to `db`) so
    constructing them per-update is negligible overhead.
  - We read `Database.db` here (infrastructure layer boundary). This is
    the *only* place outside of infrastructure/ that knows about the DB
    connection object.
  - SettingsRepository / StatsRepository are injected the same way so
    admin handlers can also be fully tested with mocks.
"""
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from infrastructure.mongo_db import Database
from infrastructure.repositories import (
    PaymentRepository,
    ProjectRepository,
    SettingsRepository,
    StatsRepository,
)


class DbInjectionMiddleware(BaseMiddleware):
    """Injects repository instances into the handler data dict."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        db = Database.db

        data["project_repo"] = ProjectRepository(db)
        data["payment_repo"] = PaymentRepository(db)
        data["stats_repo"] = StatsRepository(db)
        data["settings_repo"] = SettingsRepository(db)

        return await handler(event, data)
