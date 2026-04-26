import uuid
from typing import Any, Dict, List, Optional
import structlog

from domain.entities import AuditLog
from domain.enums import AuditEventType

logger = structlog.get_logger(__name__)

class AuditRepository:
    def __init__(self, db) -> None:
        self._db = db

    async def log_event(
        self,
        *,
        user_id: int,
        role: str,
        event_type: AuditEventType,
        entity_id: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        log_id = str(uuid.uuid4())
        audit_log = AuditLog(
            id=log_id,
            user_id=user_id,
            role=role,
            event_type=event_type,
            entity_id=entity_id,
            metadata=metadata or {},
        )
        
        await self._db.audit_logs.insert_one(audit_log.model_dump())
        logger.info(
            "Audit event logged",
            log_id=log_id,
            event_type=event_type.value,
            entity_id=entity_id,
            user_id=user_id,
        )

    async def get_logs_for_entity(self, entity_id: int) -> List[Dict[str, Any]]:
        cursor = self._db.audit_logs.find({"entity_id": int(entity_id)}).sort("created_at", -1)
        return await cursor.to_list(length=None)
