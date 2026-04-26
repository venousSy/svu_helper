from typing import Any, Dict, Optional
from domain.enums import AuditEventType
from infrastructure.repositories.audit import AuditRepository

class AuditService:
    def __init__(self, audit_repo: AuditRepository):
        self._audit_repo = audit_repo

    async def log_event(
        self,
        user_id: int,
        role: str,
        event_type: AuditEventType,
        entity_id: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        await self._audit_repo.log_event(
            user_id=user_id,
            role=role,
            event_type=event_type,
            entity_id=entity_id,
            metadata=metadata
        )
