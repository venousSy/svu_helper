# SVU Helper Bot — Project Bible
# (Add this as Source #1 in your NotebookLM notebook)

---

## What is this project?

`svu_helper` is an Arabic-language Telegram bot built for students at Syrian
Virtual University (SVU). Students use it to submit academic project requests
(e.g., assignments, reports, graduation theses) to a tutor/admin who reviews
them, sends a price offer, and delivers the finished work. The bot handles the
entire lifecycle: submission → offer → payment proof → verification → delivery.

It also includes a support ticket system so students can open conversations with
the admin directly inside Telegram.

---

## Who are the users?

| Role | What they do |
|------|-------------|
| **Student** | Submits project requests, receives offers, pays, gets delivered work |
| **Admin (tutor)** | Reviews requests, sends offers, verifies payments, uploads finished work |

Students interact entirely in Arabic. The bot is the only interface — there is
no website or mobile app.

---

## Tech Stack (final state)

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11+ |
| Telegram framework | aiogram 3.x (async, FSM-based) |
| Database | MongoDB (via Motor — async driver) |
| FSM storage | MongoDB (custom `MongoStorage` class) |
| Config management | pydantic-settings (reads `.env` file) |
| Logging | structlog (structured JSON logs) |
| Error tracking | Sentry SDK (optional) |
| Deployment | Docker + Railway cloud platform |
| Testing | pytest + Telethon (E2E tests using real Telegram API) |
| LLM integration | Google Gemini Flash Lite (LLM fuzzer for UX testing) |

---

## How the project started vs. where it ended up

The project began (commit #1, Dec 2025) as a **single 109-line Python file**
using SQLite and aiogram 2.x. By the final commit (Apr 2026) it had grown into
a **clean-architecture multi-layer application** with ~100 source files across
domain, application, infrastructure, handler, middleware, keyboard, utils, and
test layers.

### Key evolution milestones:
1. **SQLite monolith** → single `bot.py` with hardcoded admin ID and token
2. **Modularization** → split into `client.py` and `admin.py` handlers
3. **Button-driven UX** → inline keyboard offer system replaces text replies
4. **Production hardening** → Dockerfile, `.env`, payment flow, helpers
5. **MongoDB migration** → switch from SQLite to MongoDB; FSM state persisted
6. **Web dashboard** → FastAPI + React admin panel (added, then removed)
7. **Clean architecture** → domain entities, repositories, DI middleware
8. **Calendar & UX** → interactive date picker, session timeout, i18n pipeline
9. **Ticketing system** → student ↔ admin support tickets via Telegram Forums
10. **Multi-file uploads** → students can attach multiple files to a submission
11. **LLM fuzzer** → Gemini-powered bot that simulates a student to test UX

---

## Final Folder Structure

```
svu_helper/
├── main.py                  ← entry point; wires all middleware + routers
├── config.py                ← pydantic-settings; reads .env
├── states.py                ← aiogram FSM state groups
│
├── domain/                  ← pure Python; no framework dependencies
│   ├── entities.py          ← Pydantic models: Project, Payment, Ticket
│   └── enums.py             ← ProjectStatus, PaymentStatus, TicketStatus
│
├── application/             ← business logic / service layer
│   ├── project_service.py   ← add/update projects
│   ├── offer_service.py     ← create and send offers
│   ├── payment_service.py   ← verify/reject payment proofs
│   └── admin_service.py     ← stats, broadcast helpers
│
├── infrastructure/          ← all database I/O
│   ├── mongo_db.py          ← Motor client singleton
│   └── repositories/
│       ├── project.py       ← CRUD for projects collection
│       ├── payment.py       ← CRUD for payments collection
│       ├── ticket.py        ← CRUD for tickets collection
│       ├── stats.py         ← aggregation queries
│       └── settings.py      ← bot settings (e.g. maintenance mode)
│
├── handlers/                ← thin controllers; call services, send replies
│   ├── common.py            ← /start, /help, /cancel, calendar
│   ├── admin_routes/        ← dashboard, offers, payments, tickets, broadcast
│   └── client_routes/       ← submission, payment, ticket, project views
│
├── keyboards/
│   ├── factory.py           ← KeyboardFactory — all keyboards built here
│   ├── callbacks.py         ← typed callback data classes
│   └── calendar_kb.py       ← interactive calendar keyboard builder
│
├── middlewares/
│   ├── db_injection.py      ← injects repository instances into handlers
│   ├── throttling.py        ← rate limiting (0.5s between messages)
│   ├── maintenance.py       ← blocks all non-admin traffic during maintenance
│   ├── error_handler.py     ← catches all unhandled exceptions
│   ├── activity_tracker.py  ← tracks last_activity for session timeout
│   └── correlation.py       ← attaches correlation IDs to log entries
│
├── utils/
│   ├── constants.py         ← MSG_* and BTN_* constants (loaded from ar.json)
│   ├── i18n.py              ← loads locales/ar.json
│   ├── helpers.py           ← get_file_id(), notify_admins(), etc.
│   ├── formatters.py        ← format_datetime(), escape_md(), format_project_list()
│   ├── pagination.py        ← paginate() and nav keyboard builder
│   ├── broadcaster.py       ← mass-send with throttling
│   ├── storage.py           ← MongoStorage (FSM state in MongoDB)
│   └── logger.py            ← structlog setup
│
├── locales/
│   └── ar.json              ← ALL Arabic user-facing text (181 lines)
│
├── services/
│   └── ticket_service.py    ← TicketService (forum topic management)
│
├── scripts/
│   ├── llm_fuzzer.py        ← Gemini-powered UX testing bot
│   ├── wipe_db.py           ← dev utility to clear the database
│   └── generate_session_string.py  ← creates Telethon sessions for E2E tests
│
└── tests/
    ├── conftest.py
    ├── e2e_full_suite.py    ← end-to-end tests using real Telegram accounts
    ├── test_database.py
    ├── test_services.py
    ├── test_helpers.py
    ├── test_formatters.py
    ├── test_pagination.py
    └── test_stats.py
```

---

## Core Domain Models (from domain/entities.py)

### Project
The central entity. Represents one student submission.

```python
class Project(BaseModel):
    id: int
    user_id: int                        # Telegram user ID of the student
    username: Optional[str]
    user_full_name: Optional[str]
    subject_name: str                   # e.g. "Data Structures"
    tutor_name: str                     # e.g. "Dr. Ahmad"
    deadline: str                       # YYYY-MM-DD (normalized)
    details: str                        # text description
    attachments: List[dict]             # list of {file_id, file_type}
    status: ProjectStatus               # see lifecycle below
    price: Optional[str]                # set when admin sends offer
    delivery_date: Optional[str]        # set when admin sends offer
    created_at: datetime
```

### Project Lifecycle (status flow)
```
PENDING → (admin accepts) → OFFERED → (student accepts) → AWAITING_VERIFICATION
       → (admin denies)  → DENIED_ADMIN
       → (student cancels) → DENIED_STUDENT

AWAITING_VERIFICATION → (payment confirmed) → ACCEPTED → (work uploaded) → FINISHED
                      → (payment rejected)  → REJECTED_PAYMENT
```

### Payment
```python
class Payment(BaseModel):
    id: int
    project_id: int
    user_id: int
    file_id: str        # Telegram file_id for the receipt image/PDF
    file_type: str      # "photo" | "document"
    status: PaymentStatus   # pending | accepted | rejected
    created_at: datetime
```

### Ticket / TicketMessage
```python
class Ticket(BaseModel):
    ticket_id: int
    user_id: int
    message_thread_id: Optional[int]  # Telegram Forum Topic ID
    status: TicketStatus              # open | closed
    messages: List[TicketMessage]     # full conversation history

class TicketMessage(BaseModel):
    sender: str         # "user" | "admin"
    text: Optional[str]
    file_id: Optional[str]
    file_type: Optional[str]
    timestamp: datetime
```

---

## FSM States (from states.py)

Finite State Machine governs multi-step conversations.

```
Student submission flow (ProjectOrder):
  subject → tutor → deadline → details → [done button] → submitted
                                        → waiting_for_payment_proof

Admin offer flow (AdminStates):
  waiting_for_price → waiting_for_delivery → waiting_for_notes_decision
  → waiting_for_notes_text → waiting_for_finished_work

Support ticket flow (TicketStates):
  waiting_for_message   (new ticket)
  waiting_for_reply     (replying to existing ticket)
```

---

## i18n Pipeline

All Arabic text flows through a strict pipeline:

```
locales/ar.json  →  utils/i18n.py (loader)  →  utils/constants.py (MSG_*/BTN_*)  →  handlers
```

Example:
```python
# locales/ar.json
"messages": { "offer_sent": "✅ تم إرسال العرض!" }

# utils/constants.py
MSG_OFFER_SENT = _msgs["messages"]["offer_sent"]

# handlers/admin_routes/offers.py
from utils.constants import MSG_OFFER_SENT
await message.answer(MSG_OFFER_SENT)
```

---

## Middleware Stack (execution order)

Every incoming message/callback passes through these layers in order:

```
1. CorrelationLoggingMiddleware  → attaches unique request ID to logs
2. ActivityTrackerMiddleware     → updates last_activity in MongoDB
3. DbInjectionMiddleware         → creates repository instances, injects into handler
4. ThrottlingMiddleware          → rejects if < 0.5s since last message
5. MaintenanceMiddleware         → blocks non-admins during maintenance
6. GlobalErrorHandler            → catches all exceptions, notifies admins
```

---

## Configuration (.env fields)

```
BOT_TOKEN=<telegram bot token>
ADMIN_IDS=<comma-separated list of admin Telegram IDs>
MONGO_URI=<mongodb connection string>
DB_NAME=svu_helper_bot
SENTRY_DSN=<optional>
ADMIN_FORUM_GROUP_ID=<optional telegram forum group for tickets>
LOG_FILE=bot.log
```

---

## Key Architectural Rules (from AGENTS.md)

1. **Never hardcode Arabic text** — always use `locales/ar.json` → `constants.py`
2. **All keyboards via `KeyboardFactory`** — never build inline keyboards inline
3. **Handlers are thin** — extract data, call service, send reply. No business logic
4. **Services hold business logic** — validation, DB writes, notifications
5. **Repositories handle all DB I/O** — injected via middleware, never constructed in handlers
6. **Use `structlog`** — never `import logging` in handlers
7. **Use shared helpers** — `get_file_id()`, `notify_admins()`, `format_datetime()`

---

## Development Timeline

| Date | Major milestone |
|------|----------------|
| Dec 26, 2025 | First commit — 109-line SQLite bot |
| Dec 27, 2025 | Admin broadcast, modularization begins |
| Dec 28, 2025 | Button-driven offer system |
| Dec 29, 2025 | Test suite, status tracking |
| Dec 30, 2025 | Payment flow, production hardening |
| Jan 01, 2026 | Multi-admin support, MongoDB FSM |
| Jan 03, 2026 | Web dashboard added |
| Jan 05, 2026 | Web dashboard removed; security hardening |
| Jan 06, 2026 | Inline keyboards, E2E tests |
| Jan 07, 2026 | Clean architecture (domain, repos, DI) |
| Jan 08, 2026 | Interactive calendar, middleware refactor |
| Jan 09, 2026 | Ticketing system |
| Apr 22, 2026 | Multi-file uploads, i18n pipeline, LLM fuzzer |

---

## Discussion Questions for NotebookLM

1. Why did the project move from SQLite to MongoDB?
2. What problem does the DI middleware solve, and how does it work?
3. How does the bot prevent a student from accessing another student's project?
4. Why was the web dashboard added and then removed?
5. What is the FSM and why is it stored in MongoDB instead of memory?
6. How does the ticketing system use Telegram Forum topics?
7. What does the LLM fuzzer do and why was it built?
