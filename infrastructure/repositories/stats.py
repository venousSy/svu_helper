from typing import Dict
import structlog

from domain.enums import ProjectStatus

logger = structlog.get_logger()

class StatsRepository:
    def __init__(self, db) -> None:
        self._db = db

    async def get_stats(self) -> Dict[str, int]:
        pipeline = [
            {
                "$facet": {
                    "total": [{"$count": "count"}],
                    "pending": [
                        {"$match": {"status": ProjectStatus.PENDING}},
                        {"$count": "count"},
                    ],
                    "active": [
                        {
                            "$match": {
                                "status": {
                                    "$in": [
                                        ProjectStatus.ACCEPTED,
                                        ProjectStatus.AWAITING_VERIFICATION,
                                    ]
                                }
                            }
                        },
                        {"$count": "count"},
                    ],
                    "finished": [
                        {"$match": {"status": ProjectStatus.FINISHED}},
                        {"$count": "count"},
                    ],
                    "denied": [
                        {
                            "$match": {
                                "status": {
                                    "$in": [
                                        ProjectStatus.DENIED_ADMIN,
                                        ProjectStatus.DENIED_STUDENT,
                                    ]
                                }
                            }
                        },
                        {"$count": "count"},
                    ],
                }
            }
        ]

        cursor = self._db.projects.aggregate(pipeline)
        result = await cursor.to_list(length=1)

        stats = {"total": 0, "pending": 0, "active": 0, "finished": 0, "denied": 0}

        if result and result[0]:
            facets = result[0]
            for key in stats:
                if facets.get(key):
                    stats[key] = facets[key][0]["count"]

        return stats
