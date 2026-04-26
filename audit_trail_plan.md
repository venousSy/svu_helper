# Audit Trail Implementation Plan

## Goal
Implement a lightweight, professional Audit Trail in MongoDB to track critical business events (state changes) rather than raw user messages. This ensures scalability, accountability, and easier customer support troubleshooting without bloating the database.

> **NOTE:** Please delete this file (`audit_trail_plan.md`) from the project directory once the implementation is completely finished.

## Proposed Changes

---

### Domain Layer

#### [MODIFY] `domain/enums.py`
Add a new `AuditEventType` enum containing the key business events:
- `PROJECT_CREATED`
- `PROJECT_STATUS_CHANGED`
- `OFFER_SENT`
- `OFFER_ACCEPTED`
- `PAYMENT_SUBMITTED`
- `PAYMENT_APPROVED`
- `PAYMENT_REJECTED`
- `TICKET_OPENED`
- `TICKET_RESOLVED`

#### [MODIFY] `domain/entities.py`
Add the `AuditLog` Pydantic model:
- `id`: str (Unique UUID or ObjectId representation)
- `user_id`: int
- `role`: str ("student" or "admin")
- `event_type`: AuditEventType
- `entity_id`: int (The ID of the project, payment, or ticket)
- `metadata`: dict (Optional JSON to store context like old/new status or prices)
- `created_at`: datetime

---

### Infrastructure Layer

#### [NEW] `infrastructure/repositories/audit.py`
Create `AuditRepository` with methods:
- `log_event(user_id: int, role: str, event_type: AuditEventType, entity_id: int, metadata: dict = None)`
- `get_logs_for_entity(entity_id: int) -> List[dict]`

#### [MODIFY] `infrastructure/repositories/__init__.py`
Export `AuditRepository`.

---

### Middleware Layer

#### [MODIFY] `middlewares/db_injection.py`
Inject the new repository into the handler context:
- `data["audit_repo"] = AuditRepository(db)`

---

### Application Services Layer

#### [NEW] `application/audit_service.py`
Create a clean `AuditService` to wrap the repository logic (following the "Thin Handler, Fat Service" rule).

#### [MODIFY] Application & Domain Services (or Handlers)
Update the core state-changing services (or the handlers that call them) to trigger the `AuditService`.
- **`handlers/client_routes/submission.py`**: Log `PROJECT_CREATED`.
- **`handlers/client_routes/views.py`**: Log `OFFER_ACCEPTED`, `PROJECT_STATUS_CHANGED`.
- **`handlers/client_routes/payment.py`**: Log `PAYMENT_SUBMITTED`.
- **`handlers/admin_routes/dashboard.py`**: Log `OFFER_SENT`, `PROJECT_STATUS_CHANGED`, `PAYMENT_APPROVED`, `PAYMENT_REJECTED`.
- **`services/ticket_service.py`**: Log `TICKET_OPENED`, `TICKET_RESOLVED`.

## Verification Plan
1. Write unit tests for `AuditRepository` to ensure logs are correctly formatted and inserted.
2. Go through the full student flow and admin flow manually to verify the `audit_logs` collection accurately reflects the timestamp, user ID, and events generated during the test run.
