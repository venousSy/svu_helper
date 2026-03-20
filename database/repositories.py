
from typing import Any, Dict, List, Optional
from database.connection import Database
from utils.models import Project, Payment
from utils.enums import ProjectStatus, PaymentStatus

class ProjectRepository:
    @staticmethod
    async def add_project(
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
        db = Database.db
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

        document = project_model.model_dump()
        await db.projects.insert_one(document)
        return project_id

    @staticmethod
    async def get_project_by_id(project_id: int) -> Optional[Dict[str, Any]]:
        db = Database.db
        return await db.projects.find_one({"id": int(project_id)})

    @staticmethod
    async def get_user_projects(user_id: int) -> List[Dict[str, Any]]:
        db = Database.db
        cursor = db.projects.find({"user_id": user_id})
        return await cursor.to_list(length=None)

    @staticmethod
    async def update_status(project_id: int, new_status: str) -> None:
        db = Database.db
        await db.projects.update_one(
            {"id": int(project_id)}, {"$set": {"status": new_status}}
        )

    @staticmethod
    async def get_projects_by_status(statuses: List[str], user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Generic method to fetch projects by a list of statuses.
        Can optionally filter by a specific student.
        """
        db = Database.db
        query = {"status": {"$in": statuses}}
        if user_id is not None:
            query["user_id"] = user_id
            
        cursor = db.projects.find(query)
        return await cursor.to_list(length=None)

    @staticmethod
    async def update_offer(proj_id: int, price: str, delivery: str) -> None:
        db = Database.db
        await db.projects.update_one(
            {"id": int(proj_id)},
            {"$set": {"status": ProjectStatus.OFFERED, "price": price, "delivery_date": delivery}},
        )

    @staticmethod
    async def get_all_categorized() -> Dict[str, List[Dict[str, Any]]]:
        db = Database.db
        
        pending = await ProjectRepository.get_projects_by_status([ProjectStatus.PENDING])
        ongoing = await ProjectRepository.get_projects_by_status([ProjectStatus.ACCEPTED, ProjectStatus.AWAITING_VERIFICATION])
        history = await ProjectRepository.get_projects_by_status([ProjectStatus.FINISHED, ProjectStatus.DENIED_ADMIN, ProjectStatus.DENIED_STUDENT, ProjectStatus.REJECTED_PAYMENT])
        offered = await ProjectRepository.get_projects_by_status([ProjectStatus.OFFERED])
        
        return {
            "New / Pending": pending,
            "Offered / Waiting": offered,
            "Ongoing": ongoing,
            "History": history,
        }

    @staticmethod
    async def get_all_user_ids() -> List[int]:
        db = Database.db
        return await db.projects.distinct("user_id")

class PaymentRepository:
    @staticmethod
    async def add_payment(project_id: int, user_id: int, file_id: str) -> int:
        db = Database.db
        payment_id = await Database.get_next_sequence("payment_id")
        
        payment_model = Payment(
            id=payment_id,
            project_id=int(project_id),
            user_id=user_id,
            file_id=file_id,
            status=PaymentStatus.PENDING
        )
        
        document = payment_model.model_dump()
        await db.payments.insert_one(document)
        return payment_id

    @staticmethod
    async def get_payment(payment_id: int) -> Optional[Dict[str, Any]]:
        db = Database.db
        return await db.payments.find_one({"id": int(payment_id)})

    @staticmethod
    async def update_status(payment_id: int, new_status: str) -> None:
        db = Database.db
        await db.payments.update_one(
            {"id": int(payment_id)}, {"$set": {"status": new_status}}
        )

    @staticmethod
    async def get_all() -> List[Dict[str, Any]]:
        db = Database.db
        return await db.payments.find().sort("id", -1).to_list(length=None)

class StatsRepository:
    @staticmethod
    async def get_stats() -> Dict[str, int]:
        db = Database.db
        
        pipeline = [
            {"$facet": {
                "total": [{"$count": "count"}],
                "pending": [{"$match": {"status": ProjectStatus.PENDING}}, {"$count": "count"}],
                "active": [{"$match": {"status": {"$in": [ProjectStatus.ACCEPTED, ProjectStatus.AWAITING_VERIFICATION]}}}, {"$count": "count"}],
                "finished": [{"$match": {"status": ProjectStatus.FINISHED}}, {"$count": "count"}],
                "denied": [{"$match": {"status": {"$in": [ProjectStatus.DENIED_ADMIN, ProjectStatus.DENIED_STUDENT]}}}, {"$count": "count"}]
            }}
        ]
        
        cursor = db.projects.aggregate(pipeline)
        result = await cursor.to_list(length=1)
        
        stats = {"total": 0, "pending": 0, "active": 0, "finished": 0, "denied": 0}
        
        if result and result[0]:
            facets = result[0]
            for key in stats.keys():
                if facets.get(key) and len(facets[key]) > 0:
                    stats[key] = facets[key][0]["count"]
                    
        return stats

class SettingsRepository:
    @staticmethod
    async def get_maintenance_mode() -> bool:
        db = Database.db
        doc = await db.settings.find_one({"_id": "global_config"})
        return doc.get("maintenance_mode", False) if doc else False

    @staticmethod
    async def set_maintenance_mode(status: bool) -> None:
        db = Database.db
        await db.settings.update_one(
            {"_id": "global_config"},
            {"$set": {"maintenance_mode": status}},
            upsert=True
        )
