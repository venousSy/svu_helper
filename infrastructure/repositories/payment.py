from typing import Any, Dict, List, Optional
import structlog

from domain.entities import Payment
from domain.enums import PaymentStatus
from infrastructure.mongo_db import Database

logger = structlog.get_logger()

DEFAULT_PAGE_SIZE: int = 500
MAX_PAGE_SIZE: int = 500

class PaymentRepository:
    def __init__(self, db) -> None:
        self._db = db

    async def add_payment(
        self, project_id: int, user_id: int, file_id: str, file_type: Optional[str] = None
    ) -> int:
        payment_id = await Database.get_next_sequence("payment_id")

        payment_model = Payment(
            id=payment_id,
            project_id=int(project_id),
            user_id=user_id,
            file_id=file_id,
            file_type=file_type,
            status=PaymentStatus.PENDING,
        )

        await self._db.payments.insert_one(payment_model.model_dump())
        logger.info("Payment reference created in DB", payment_id=payment_id, project_id=project_id)
        return payment_id

    async def get_payment(self, payment_id: int) -> Optional[Dict[str, Any]]:
        return await self._db.payments.find_one({"id": int(payment_id)})

    async def get_payment_by_project_id(self, project_id: int) -> Optional[Dict[str, Any]]:
        return await self._db.payments.find_one({"project_id": int(project_id)})

    async def update_status(self, payment_id: int, new_status: str) -> None:
        await self._db.payments.update_one(
            {"id": int(payment_id)}, {"$set": {"status": new_status}}
        )
        logger.info("Payment status updated in DB", payment_id=payment_id, new_status=new_status)

    async def get_all(
        self,
        *,
        limit: int = DEFAULT_PAGE_SIZE,
        skip: int = 0,
    ) -> List[Dict[str, Any]]:
        limit = min(limit, MAX_PAGE_SIZE)
        pipeline = [
            {
                "$lookup": {
                    "from": "projects",
                    "localField": "project_id",
                    "foreignField": "id",
                    "as": "project"
                }
            },
            {
                "$unwind": {
                    "path": "$project",
                    "preserveNullAndEmptyArrays": True
                }
            },
            {
                "$addFields": {
                    "project_name": "$project.subject_name",
                    "username": "$project.username",
                    "user_full_name": "$project.user_full_name",
                    "is_pending": {"$cond": [{"$eq": ["$status", "pending"]}, 1, 0]}
                }
            },
            {
                "$project": {
                    "project": 0
                }
            },
            {
                "$sort": {
                    "is_pending": -1,
                    "id": -1
                }
            },
            { "$skip": skip },
            { "$limit": limit }
        ]
        cursor = self._db.payments.aggregate(pipeline)
        return await cursor.to_list(length=limit)
