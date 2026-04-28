from typing import Any, Dict, List, Optional
import structlog

from domain.entities import Project
from domain.enums import ProjectStatus
from infrastructure.mongo_db import Database

logger = structlog.get_logger()

DEFAULT_PAGE_SIZE: int = 500
MAX_PAGE_SIZE: int = 500

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
        attachments: List[dict],
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
            attachments=attachments,
        )

        await self._db.projects.insert_one(project_model.model_dump())
        logger.info("Project created in DB", project_id=project_id, user_id=user_id)
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
        limit = min(limit, MAX_PAGE_SIZE)
        logger.debug("Fetching user projects from DB", user_id=user_id, limit=limit, skip=skip)
        cursor = self._db.projects.find({"user_id": user_id}).sort("id", -1).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)

    async def update_status(self, project_id: int, new_status: str) -> None:
        await self._db.projects.update_one(
            {"id": int(project_id)}, {"$set": {"status": new_status}}
        )
        logger.info("Project status updated in DB", project_id=project_id, new_status=new_status)

    async def get_projects_by_status(
        self,
        statuses: List[str],
        user_id: Optional[int] = None,
        *,
        limit: int = DEFAULT_PAGE_SIZE,
        skip: int = 0,
    ) -> List[Dict[str, Any]]:
        limit = min(limit, MAX_PAGE_SIZE)
        query: Dict[str, Any] = {"status": {"$in": statuses}}
        if user_id is not None:
            query["user_id"] = user_id
        cursor = self._db.projects.find(query).sort("id", -1).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)

    async def update_offer(self, proj_id: int, price: int, delivery: str) -> None:
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
        logger.info("Project offer updated in DB", project_id=proj_id, price=price)

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
