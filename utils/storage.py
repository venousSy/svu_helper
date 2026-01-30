
from typing import Any, Dict, Optional

from aiogram.fsm.storage.base import BaseStorage, StateType, StorageKey
from motor.motor_asyncio import AsyncIOMotorClient

class MongoStorage(BaseStorage):
    """
    MongoDB-based storage for FSM state and data.
    """
    def __init__(self, mongo_client: AsyncIOMotorClient, db_name: str = "svu_bot_db", collection_name: str = "fsm_states"):
        self.client = mongo_client
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        chat_id = key.chat_id
        user_id = key.user_id
        
        # We store by user_id and chat_id combination
        filter_query = {"chat_id": chat_id, "user_id": user_id}
        
        if state is None:
            await self.collection.update_one(filter_query, {"$unset": {"state": ""}}, upsert=True)
        else:
            await self.collection.update_one(filter_query, {"$set": {"state": state.state if hasattr(state, 'state') else str(state)}}, upsert=True)

    async def get_state(self, key: StorageKey) -> Optional[str]:
        chat_id = key.chat_id
        user_id = key.user_id
        filter_query = {"chat_id": chat_id, "user_id": user_id}
        
        doc = await self.collection.find_one(filter_query)
        return doc.get("state") if doc else None

    async def set_data(self, key: StorageKey, data: Dict[str, Any]) -> None:
        chat_id = key.chat_id
        user_id = key.user_id
        filter_query = {"chat_id": chat_id, "user_id": user_id}
        
        await self.collection.update_one(filter_query, {"$set": {"data": data}}, upsert=True)

    async def get_data(self, key: StorageKey) -> Dict[str, Any]:
        chat_id = key.chat_id
        user_id = key.user_id
        filter_query = {"chat_id": chat_id, "user_id": user_id}
        
        doc = await self.collection.find_one(filter_query)
        return doc.get("data", {}) if doc else {}

    async def close(self) -> None:
        # We don't close the client here because it's shared
        pass
