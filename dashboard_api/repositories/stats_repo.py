from typing import List, Dict, Any, Optional
from infrastructure.mongo_db import get_db
from datetime import datetime, timezone
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

async def aggregate_project_volume(start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
    db = await get_db()
    match = {}
    if start_date or end_date:
        match["created_at"] = {}
        if start_date:
            dt = _parse_date(start_date)
            if dt:
                match["created_at"]["$gte"] = dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
        if end_date:
            dt = _parse_date(end_date)
            if dt:
                match["created_at"]["$lte"] = datetime.combine(dt.date(), datetime.max.time(), tzinfo=timezone.utc)
        if not match["created_at"]:
            del match["created_at"]
    
    pipeline = []
    if match:
        pipeline.append({"$match": match})
        
    pipeline.extend([
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%d", 
                        "date": {"$toDate": "$created_at"},
                        "onNull": "unknown"
                    }
                },
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"_id": 1}}
    ])
    cursor = db.projects.aggregate(pipeline)
    return await cursor.to_list(length=None)

async def aggregate_conversion_rates(start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
    db = await get_db()
    match = {}
    if start_date or end_date:
        match["created_at"] = {}
        if start_date:
            dt = _parse_date(start_date)
            if dt:
                match["created_at"]["$gte"] = dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
        if end_date:
            dt = _parse_date(end_date)
            if dt:
                match["created_at"]["$lte"] = datetime.combine(dt.date(), datetime.max.time(), tzinfo=timezone.utc)
        if not match["created_at"]:
            del match["created_at"]
            
    pipeline = []
    if match:
        pipeline.append({"$match": match})
        
    pipeline.append({
        "$group": {
            "_id": "$status",
            "count": {"$sum": 1}
        }
    })
    cursor = db.projects.aggregate(pipeline)
    return await cursor.to_list(length=None)

async def aggregate_revenue_over_time(start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
    """Revenue grouped by day.  Handles price stored as string OR number."""
    db = await get_db()
    _price_as_num = {
        "$convert": {"input": "$price", "to": "double", "onError": 0, "onNull": 0}
    }
    match = {
        "status": {"$in": ["finished", "accepted"]}
    }
    if start_date or end_date:
        match["created_at"] = {}
        if start_date:
            dt = _parse_date(start_date)
            if dt:
                match["created_at"]["$gte"] = dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
        if end_date:
            dt = _parse_date(end_date)
            if dt:
                match["created_at"]["$lte"] = datetime.combine(dt.date(), datetime.max.time(), tzinfo=timezone.utc)
        if not match["created_at"]:
            del match["created_at"]
            
    pipeline = [
        {"$match": match},
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%d", 
                        "date": {"$toDate": "$created_at"},
                        "onNull": "unknown"
                    }
                },
                "revenue": {"$sum": _price_as_num}
            }
        },
        {"$sort": {"_id": 1}}
    ]
    cursor = db.projects.aggregate(pipeline)
    return await cursor.to_list(length=None)

async def aggregate_top_referrers(limit: int = 5) -> List[Dict[str, Any]]:
    db = await get_db()
    pipeline = [
        {"$match": {"referred_by": {"$ne": None}}},
        {"$group": {"_id": "$referred_by", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": limit},
        {"$lookup": {
            "from": "users",
            "localField": "_id",
            "foreignField": "user_id",
            "as": "user_info"
        }},
        {"$unwind": {"path": "$user_info", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "_id": 1,
            "count": 1,
            "username": "$user_info.username",
            "full_name": "$user_info.full_name"
        }}
    ]
    cursor = db.referral_users.aggregate(pipeline)
    return await cursor.to_list(length=None)


async def aggregate_total_revenue() -> float:
    """Returns the grand-total revenue across all accepted/finished projects."""
    db = await get_db()
    _price_as_num = {
        "$convert": {"input": "$price", "to": "double", "onError": 0, "onNull": 0}
    }
    pipeline = [
        {"$match": {"status": {"$in": ["finished", "accepted"]}}},
        {"$group": {"_id": None, "total": {"$sum": _price_as_num}}},
    ]
    cursor = db.projects.aggregate(pipeline)
    result = await cursor.to_list(length=1)
    return result[0]["total"] if result else 0.0
