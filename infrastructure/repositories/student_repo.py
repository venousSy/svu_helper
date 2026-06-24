from typing import Optional

from domain.entities import StudentProfile
from infrastructure.mongo_db import Database

class StudentRepository:
    """Repository for managing student profiles."""
    
    def __init__(self, db) -> None:
        self._db = db

    async def get_profile(self, user_id: int) -> Optional[StudentProfile]:
        """Fetch a student's profile."""
        doc = await self._db.students.find_one({"user_id": user_id})
        if doc:
            return StudentProfile(**doc)
        return None

    async def create_profile(self, user_id: int, specialization: str) -> StudentProfile:
        """Create or update a student's profile."""
        profile = StudentProfile(user_id=user_id, specialization=specialization)
        
        await self._db.students.update_one(
            {"user_id": user_id},
            {"$set": profile.model_dump()},
            upsert=True
        )
        return profile
