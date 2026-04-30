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
    db = await get_db()
    pipeline = [
        {
            "$match": {
                "status": {"$in": ["finished", "accepted"]},
                "price": {"$ne": None}
            }
        },
        {
            "$group": {
                "_id": {
                    "$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}
                },
                "revenue": {"$sum": "$price"}
            }
        },
        {"$sort": {"_id": 1}}
    ]
    cursor = db.projects.aggregate(pipeline)
    return await cursor.to_list(length=None)
