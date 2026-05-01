from typing import List, Dict, Any
from infrastructure.mongo_db import get_db

async def aggregate_project_volume() -> List[Dict[str, Any]]:
    db = await get_db()
    pipeline = [
        {
            "$group": {
                "_id": {
                    "$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}
                },
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"_id": 1}}
    ]
    cursor = db.projects.aggregate(pipeline)
    return await cursor.to_list(length=None)

async def aggregate_conversion_rates() -> List[Dict[str, Any]]:
    db = await get_db()
    pipeline = [
        {
            "$group": {
                "_id": "$status",
                "count": {"$sum": 1}
            }
        }
    ]
    cursor = db.projects.aggregate(pipeline)
    return await cursor.to_list(length=None)

async def aggregate_revenue_over_time() -> List[Dict[str, Any]]:
    """Revenue grouped by day.  Handles price stored as string OR number."""
    db = await get_db()
    _price_as_num = {
        "$convert": {"input": "$price", "to": "double", "onError": 0, "onNull": 0}
    }
    pipeline = [
        {
            "$match": {
                "status": {"$in": ["finished", "accepted"]},
            }
        },
        {
            "$group": {
                "_id": {
                    "$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}
                },
                "revenue": {"$sum": _price_as_num}
            }
        },
        {"$sort": {"_id": 1}}
    ]
    cursor = db.projects.aggregate(pipeline)
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
