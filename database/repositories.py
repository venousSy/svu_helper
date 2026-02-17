
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
    async def get_pending() -> List[Dict[str, Any]]:
        db = Database.db
        return await db.projects.find({"status": ProjectStatus.PENDING}).to_list(length=None)
        
    @staticmethod
    async def get_student_offers(user_id: int) -> List[Dict[str, Any]]:
        db = Database.db
        return await db.projects.find({"user_id": user_id, "status": ProjectStatus.OFFERED}).to_list(length=None)
        
    @staticmethod
    async def update_offer(proj_id: int, price: str, delivery: str) -> None:
        db = Database.db
        await db.projects.update_one(
            {"id": int(proj_id)},
            {"$set": {"status": ProjectStatus.OFFERED, "price": price, "delivery_date": delivery}},
        )

    @staticmethod
    async def get_accepted() -> List[Dict[str, Any]]:
        db = Database.db
        return await db.projects.find({"status": ProjectStatus.ACCEPTED}).to_list(length=None)

    @staticmethod
    async def get_history() -> List[Dict[str, Any]]:
        db = Database.db
        return await db.projects.find({
            "status": {
                "$in": [
                    ProjectStatus.FINISHED,
                    ProjectStatus.DENIED_ADMIN,
                    ProjectStatus.DENIED_STUDENT,
                    ProjectStatus.REJECTED_PAYMENT,
                ]
            }
        }).to_list(length=None)
        
    @staticmethod
    async def get_all_categorized() -> Dict[str, List[Dict[str, Any]]]:
        db = Database.db
        # This logic was in get_all_projects_categorized
        # We can implement it here or reuse existing methods if careful
        
        pending = await db.projects.find({"status": ProjectStatus.PENDING}).to_list(length=None)
        ongoing = await db.projects.find(
            {"status": {"$in": [ProjectStatus.ACCEPTED, ProjectStatus.AWAITING_VERIFICATION]}}
        ).to_list(length=None)
        history = await db.projects.find(
            {"status": {"$in": [ProjectStatus.FINISHED, ProjectStatus.DENIED_ADMIN, ProjectStatus.DENIED_STUDENT, ProjectStatus.REJECTED_PAYMENT]}}
        ).to_list(length=None)
        offered = await db.projects.find({"status": ProjectStatus.OFFERED}).to_list(length=None)
        
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
        async def count(query):
            return await db.projects.count_documents(query)
            
        stats = {
            "total": await count({}),
            "pending": await count({"status": ProjectStatus.PENDING}),
            "active": await count({"status": {"$in": [ProjectStatus.ACCEPTED, ProjectStatus.AWAITING_VERIFICATION]}}),
            "finished": await count({"status": ProjectStatus.FINISHED}),
            "denied": await count({"status": {"$in": [ProjectStatus.DENIED_ADMIN, ProjectStatus.DENIED_STUDENT]}})
        }
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
