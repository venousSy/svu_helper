from datetime import datetime, timezone
import structlog
from infrastructure.mongo_db import get_db

logger = structlog.get_logger(__name__)

class E2ETestRepo:
    @staticmethod
    async def save_test_run(suites_results: dict):
        """
        Saves the test results dict.
        suites_results is expected to be a dict:
        {"general": "passed", "matchmaking": "failed", ...}
        """
        db = await get_db()
        await db.e2e_test_results.update_one(
            {"_id": "latest"},
            {
                "$set": {
                    "updated_at": datetime.now(timezone.utc),
                    "suites": suites_results
                }
            },
            upsert=True
        )

    @staticmethod
    async def get_last_test_run() -> dict:
        """
        Returns the suites dictionary of the last run.
        """
        db = await get_db()
        doc = await db.e2e_test_results.find_one({"_id": "latest"})
        if doc and "suites" in doc:
            return doc["suites"]
        return {}
