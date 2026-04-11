class SettingsRepository:
    def __init__(self, db) -> None:
        self._db = db

    async def get_maintenance_mode(self) -> bool:
        doc = await self._db.settings.find_one({"_id": "global_config"})
        return doc.get("maintenance_mode", False) if doc else False

    async def set_maintenance_mode(self, status: bool) -> None:
        await self._db.settings.update_one(
            {"_id": "global_config"},
            {"$set": {"maintenance_mode": status}},
            upsert=True,
        )
