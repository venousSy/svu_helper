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
    TicketRepository,
    AuditRepository,
)
from infrastructure.repositories.peer_repo import (
    StudentProfileRepository,
    ProjectAdRepository,
    MatchRequestRepository,
    CourseCatalogRepository,
)
from application.peer_service import PeerService


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
        data["ticket_repo"] = TicketRepository(db)
        data["audit_repo"] = AuditRepository(db)

        # Peer-Link Repositories
        student_repo = StudentProfileRepository(db)
        ad_repo = ProjectAdRepository(db)
        match_repo = MatchRequestRepository(db)
        catalog_repo = CourseCatalogRepository(db)

        data["student_repo"] = student_repo
        data["ad_repo"] = ad_repo
        data["match_repo"] = match_repo
        data["catalog_repo"] = catalog_repo
        data["peer_service"] = PeerService(
            student_repo=student_repo,
            ad_repo=ad_repo,
            match_repo=match_repo,
            catalog_repo=catalog_repo,
        )

        return await handler(event, data)
