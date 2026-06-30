from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from infrastructure.mongo_db import get_db
import structlog

logger = structlog.get_logger(__name__)

def _parse_date(date_str: str) -> Optional[datetime]:
    if not date_str: return None
    date_str = date_str.strip().split('T')[0]
    for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d']:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(date_str)
    except ValueError as e:
        logger.error("Failed to parse date", error=str(e), date_str=date_str)
        return None

async def count_projects(
    status_filter: Optional[str] = None, 
    search_student_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> int:
    db = await get_db()
    query = {}
    if status_filter:
        query["status"] = status_filter
    if search_student_id:
        query["user_id"] = search_student_id
    if start_date or end_date:
        query["created_at"] = {}
        if start_date:
            dt = _parse_date(start_date)
            if dt:
                query["created_at"]["$gte"] = dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
        if end_date:
            dt = _parse_date(end_date)
            if dt:
                query["created_at"]["$lte"] = datetime.combine(dt.date(), datetime.max.time(), tzinfo=timezone.utc)
        if not query["created_at"]:
            del query["created_at"]
    
    return await db.projects.count_documents(query)

async def get_paginated_projects(
    skip: int, 
    limit: int, 
    status_filter: Optional[str] = None, 
    search_student_id: Optional[int] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    db = await get_db()
    query = {}
    if status_filter:
        query["status"] = status_filter
    if search_student_id:
        query["user_id"] = search_student_id
    if start_date or end_date:
        query["created_at"] = {}
        if start_date:
            dt = _parse_date(start_date)
            if dt:
                query["created_at"]["$gte"] = dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
        if end_date:
            dt = _parse_date(end_date)
            if dt:
                query["created_at"]["$lte"] = datetime.combine(dt.date(), datetime.max.time(), tzinfo=timezone.utc)
        if not query["created_at"]:
            del query["created_at"]
            
    sort_direction = -1 if sort_order == "desc" else 1
    # Ensure safe sort field
    valid_sort_fields = ["created_at", "price", "status", "user_id", "id"]
    if sort_by not in valid_sort_fields:
        sort_by = "created_at"
        
    cursor = db.projects.find(query).sort(sort_by, sort_direction).skip(skip)
    if limit > 0:
        cursor = cursor.limit(limit)
        
    # to_list requires a length, if no limit we can use None or a large number
    return await cursor.to_list(length=None)
