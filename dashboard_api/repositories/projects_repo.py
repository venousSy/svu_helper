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

from datetime import datetime, timedelta, timezone

async def get_urgent_projects() -> List[Dict[str, Any]]:
    db = await get_db()
    now = datetime.now(timezone.utc)
    six_hours_ago = now - timedelta(hours=6)
    two_days_from_now = (now + timedelta(days=2)).strftime("%Y-%m-%d")
    
    pending_urgent_cursor = db.projects.find({
        "status": "pending",
        "created_at": {"$lte": six_hours_ago}
    })
    
    awaiting_urgent_cursor = db.projects.aggregate([
        {"$match": {"status": "awaiting_verification"}},
        {"$lookup": {
            "from": "payments",
            "localField": "id",
            "foreignField": "project_id",
            "as": "payment_info"
        }},
        {"$unwind": {"path": "$payment_info", "preserveNullAndEmptyArrays": True}},
        {"$match": {
            "payment_info.created_at": {"$lte": six_hours_ago}
        }},
        {"$project": {"payment_info": 0}}
    ])
    
    delivery_urgent_cursor = db.projects.find({
        "status": {"$in": ["accepted", "offered"]},
        "delivery_date": {"$ne": None, "$lte": two_days_from_now}
    })
    
    pending_projects = await pending_urgent_cursor.to_list(length=100)
    awaiting_projects = await awaiting_urgent_cursor.to_list(length=100)
    delivery_projects = await delivery_urgent_cursor.to_list(length=100)
    
    all_urgent = {p["id"]: p for p in pending_projects + awaiting_projects + delivery_projects}
    
    return sorted(list(all_urgent.values()), key=lambda x: x["created_at"], reverse=True)
