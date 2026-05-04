from typing import List, Dict, Any, Optional
from infrastructure.mongo_db import get_db

async def count_projects(status_filter: Optional[str] = None, search_student_id: Optional[int] = None) -> int:
    db = await get_db()
    query = {}
    if status_filter:
        query["status"] = status_filter
    if search_student_id:
        query["user_id"] = search_student_id
    
    return await db.projects.count_documents(query)

async def get_paginated_projects(skip: int, limit: int, status_filter: Optional[str] = None, search_student_id: Optional[int] = None) -> List[Dict[str, Any]]:
    db = await get_db()
    query = {}
    if status_filter:
        query["status"] = status_filter
    if search_student_id:
        query["user_id"] = search_student_id
        
    cursor = db.projects.find(query).sort("created_at", -1).skip(skip).limit(limit)
    return await cursor.to_list(length=limit)
