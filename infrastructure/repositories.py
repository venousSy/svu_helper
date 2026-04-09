"""
Infrastructure – Repository Implementations
============================================
All repositories accept a `db` handle via constructor injection.
This removes the hidden dependency on `Database.db` class variable and
makes every repository trivially mockable in unit tests:

    repo = ProjectRepository(mock_db)

Handlers receive pre-built repository instances through the
DbInjectionMiddleware (middlewares/db_injection.py) which populates
the aiogram data dict before each handler call.
"""
from typing import Any, Dict, List, Optional, Tuple

from domain.entities import Payment, Project
from domain.enums import PaymentStatus, ProjectStatus
from infrastructure.mongo_db import Database


# ---------------------------------------------------------------------------
# Pagination defaults
# ---------------------------------------------------------------------------

#: Maximum documents returned in a single paginated query.
#: Prevents accidental full-collection loads when callers omit a limit.
DEFAULT_PAGE_SIZE: int = 15
MAX_PAGE_SIZE: int = 500


# ---------------------------------------------------------------------------
# ProjectRepository
# ---------------------------------------------------------------------------

class ProjectRepository:
    def __init__(self, db) -> None:
        self._db = db

    async def add_project(
        self,
        *,
        user_id: int,
        username: str,
        user_full_name: str,
        subject: str,
        tutor: str,
        deadline: str,
        details: str,
        file_id: Optional[str],
        file_type: Optional[str],
    ) -> int:
        project_id = await Database.get_next_sequence("project_id")

        project_model = Project(
            id=project_id,
            user_id=user_id,
            username=username,
            user_full_name=user_full_name,
            subject_name=subject,
            tutor_name=tutor,
            deadline=deadline,
            details=details,
            file_id=file_id,
            file_type=file_type,
        )

        await self._db.projects.insert_one(project_model.model_dump())
        return project_id

    async def get_project_by_id(self, project_id: int) -> Optional[Dict[str, Any]]:
        return await self._db.projects.find_one({"id": int(project_id)})

    async def get_user_projects(
        self,
        user_id: int,
        *,
        limit: int = DEFAULT_PAGE_SIZE,
        skip: int = 0,
    ) -> List[Dict[str, Any]]:
        """Returns projects owned by *user_id*, newest-first, with pagination.

        Args:
            user_id: Telegram user id to filter by.
            limit: Maximum number of documents to return (default 100, max 500).
            skip:  Number of documents to skip (for offset-based paging).
        """
        limit = min(limit, MAX_PAGE_SIZE)
        cursor = self._db.projects.find({"user_id": user_id}).sort("id", -1).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)

    async def update_status(self, project_id: int, new_status: str) -> None:
        await self._db.projects.update_one(
            {"id": int(project_id)}, {"$set": {"status": new_status}}
        )

    async def get_projects_by_status(
        self,
        statuses: List[str],
        user_id: Optional[int] = None,
        *,
        limit: int = DEFAULT_PAGE_SIZE,
        skip: int = 0,
    ) -> List[Dict[str, Any]]:
        """Fetches projects filtered by one or more status values.

        Args:
            statuses: List of :class:`~domain.enums.ProjectStatus` values to match.
            user_id:  If provided, further filters results to this Telegram user.
            limit:    Maximum documents to return per page (default 100, max 500).
            skip:     Documents to skip for offset-based pagination.
        """
        limit = min(limit, MAX_PAGE_SIZE)
        query: Dict[str, Any] = {"status": {"$in": statuses}}
        if user_id is not None:
            query["user_id"] = user_id
        cursor = self._db.projects.find(query).sort("id", -1).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)

    async def update_offer(self, proj_id: int, price: str, delivery: str) -> None:
        await self._db.projects.update_one(
            {"id": int(proj_id)},
            {
                "$set": {
                    "status": ProjectStatus.OFFERED,
                    "price": price,
                    "delivery_date": delivery,
                }
            },
        )

    async def get_all_categorized(self) -> Dict[str, List[Dict[str, Any]]]:
        pending = await self.get_projects_by_status([ProjectStatus.PENDING])
        ongoing = await self.get_projects_by_status(
            [ProjectStatus.ACCEPTED, ProjectStatus.AWAITING_VERIFICATION]
        )
        history = await self.get_projects_by_status(
            [
                ProjectStatus.FINISHED,
                ProjectStatus.DENIED_ADMIN,
                ProjectStatus.DENIED_STUDENT,
                ProjectStatus.REJECTED_PAYMENT,
            ]
        )
        offered = await self.get_projects_by_status([ProjectStatus.OFFERED])

        return {
            "New / Pending": pending,
            "Offered / Waiting": offered,
            "Ongoing": ongoing,
            "History": history,
        }

    async def get_all_user_ids(self) -> List[int]:
        return await self._db.projects.distinct("user_id")


# ---------------------------------------------------------------------------
# PaymentRepository
# ---------------------------------------------------------------------------

class PaymentRepository:
    def __init__(self, db) -> None:
        self._db = db

    async def add_payment(
        self, project_id: int, user_id: int, file_id: str
    ) -> int:
        payment_id = await Database.get_next_sequence("payment_id")

        payment_model = Payment(
            id=payment_id,
            project_id=int(project_id),
            user_id=user_id,
            file_id=file_id,
            status=PaymentStatus.PENDING,
        )

        await self._db.payments.insert_one(payment_model.model_dump())
        return payment_id

    async def get_payment(self, payment_id: int) -> Optional[Dict[str, Any]]:
        return await self._db.payments.find_one({"id": int(payment_id)})

    async def update_status(self, payment_id: int, new_status: str) -> None:
        await self._db.payments.update_one(
            {"id": int(payment_id)}, {"$set": {"status": new_status}}
        )

    async def get_all(
        self,
        *,
        limit: int = DEFAULT_PAGE_SIZE,
        skip: int = 0,
    ) -> List[Dict[str, Any]]:
        """Returns payments sorted newest-first with pagination.

        Args:
            limit: Maximum documents to return (default 100, max 500).
            skip:  Documents to skip for offset-based paging.
        """
        limit = min(limit, MAX_PAGE_SIZE)
        cursor = self._db.payments.find().sort("id", -1).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)


# ---------------------------------------------------------------------------
# StatsRepository
# ---------------------------------------------------------------------------

class StatsRepository:
    def __init__(self, db) -> None:
        self._db = db

    async def get_stats(self) -> Dict[str, int]:
        pipeline = [
            {
                "$facet": {
                    "total": [{"$count": "count"}],
                    "pending": [
                        {"$match": {"status": ProjectStatus.PENDING}},
                        {"$count": "count"},
                    ],
                    "active": [
                        {
                            "$match": {
                                "status": {
                                    "$in": [
                                        ProjectStatus.ACCEPTED,
                                        ProjectStatus.AWAITING_VERIFICATION,
                                    ]
                                }
                            }
                        },
                        {"$count": "count"},
                    ],
                    "finished": [
                        {"$match": {"status": ProjectStatus.FINISHED}},
                        {"$count": "count"},
                    ],
                    "denied": [
                        {
                            "$match": {
                                "status": {
                                    "$in": [
                                        ProjectStatus.DENIED_ADMIN,
                                        ProjectStatus.DENIED_STUDENT,
                                    ]
                                }
                            }
                        },
                        {"$count": "count"},
                    ],
                }
            }
        ]

        cursor = self._db.projects.aggregate(pipeline)
        result = await cursor.to_list(length=1)

        stats = {"total": 0, "pending": 0, "active": 0, "finished": 0, "denied": 0}

        if result and result[0]:
            facets = result[0]
            for key in stats:
                if facets.get(key):
                    stats[key] = facets[key][0]["count"]

        return stats


# ---------------------------------------------------------------------------
# SettingsRepository
# ---------------------------------------------------------------------------

class SettingsRepository:
    def __init__(self, db) -> None:
        self._db = db

    async def get_maintenance_mode(self) -> bool:
        doc = await self._db.settings.find_one({"_id": "global_config"})
        return doc.get("maintenance_mode", False) if doc else False

    async def set_maintenance_mode(self, status: bool) -> None:
        await self._db.settings.update_one(
            {"_id": "global_config"},
            {"$set": {"maintenance_mode": status}},
            upsert=True,
        )
