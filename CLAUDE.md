# SVU Helper Bot — Agent Guidelines

> **READ THIS BEFORE WRITING ANY CODE.**
> This file defines the mandatory architectural patterns for the SVU Helper Bot.
> Every AI agent working on this codebase MUST follow these rules.

---

## 1. User-Facing Text: The i18n Pipeline

**NEVER hard-code Arabic (or any) user-facing text in handler or service files.**

The text pipeline is:

```
locales/ar.json  →  utils/i18n.py (loader)  →  utils/constants.py (MSG_* / BTN_*)  →  handlers
```

### When adding a new message

1. **Add the key to `locales/ar.json`** under the correct section:
   - `messages.*` — admin/system messages
   - `client_prompts.*` — student-facing prompts
   - `buttons.*` — button labels
   - `status.*` — project status labels
2. **Add a `MSG_*` or `BTN_*` constant** in `utils/constants.py` that reads from `_msgs`:
   ```python
   MSG_MY_NEW_MESSAGE = _msgs["messages"]["my_new_key"]
   ```
3. **Import the constant** in your handler:
   ```python
   from utils.constants import MSG_MY_NEW_MESSAGE
   ```

### Rules
- All `MSG_*` constants use Python `.format()` placeholders (`{}`), not f-strings.
- Button labels (`BTN_*`) are plain strings — no formatting placeholders.
- Inline keyboard button text that is purely structural (icons, IDs) may be built in `keyboards/factory.py` directly, but any translatable word must come from `ar.json`.

---

## 2. Shared Helpers — Use Them, Don't Reinvent Them

Before writing any utility logic, check if a helper already exists.

### `utils/helpers.py` — Message & Media Helpers

| Function | Purpose | Use instead of… |
|----------|---------|-----------------|
| `get_file_id(message)` | Returns `(file_id, file_type)` from any media message | Manual `message.photo[-1].file_id` checks |
| `get_file_size(message)` | Returns file size regardless of media type | Manual `message.document.file_size` checks |
| `extract_message_content(message)` | Returns `(text, file_id, file_type)` — full extraction | Writing your own `_extract_content` |
| `notify_admins(bot, text, ...)` | Sends a message to all configured admins | `for admin_id in settings.admin_ids` loops |
| `build_ticket_service(ticket_repo, bot)` | Creates a `TicketService` with forum config | Inline `TicketService(...)` construction |

### `utils/formatters.py` — Display Formatting

| Function | Purpose | Use instead of… |
|----------|---------|-----------------|
| `format_datetime(value, fmt)` | Safe datetime → string with fallback | `hasattr(x, "strftime")` blocks |
| `escape_md(text)` | Escapes Markdown special chars | Manual `.replace("_", "\\_")` |
| `format_project_list(...)` | Paginated project list text | Custom list formatting |
| `format_admin_notification(...)` | New-project admin alert text | Inline f-string construction |

### `utils/pagination.py`

| Function | Purpose |
|----------|---------|
| `paginate(items, page)` | Returns `(slice, page, total_pages)` |
| `build_nav_keyboard(...)` | Builds ◀️ ▶️ navigation keyboard |

### `utils/broadcaster.py`

| Function | Purpose |
|----------|---------|
| `Broadcaster(bot).broadcast(users, text)` | Mass-send with throttling |

**Rule:** If you need a helper that doesn't exist, add it to the appropriate `utils/` module — do NOT create local `_helper` functions inside handlers.

---

## 3. Keyboards — Use `KeyboardFactory`

All keyboards are built through `keyboards/factory.py → KeyboardFactory`.

```python
# ✅ Correct
from keyboards.factory import KeyboardFactory
kb = KeyboardFactory.admin_dashboard()
kb = KeyboardFactory.manage_project(proj_id)
kb = KeyboardFactory.offer_actions(proj_id)

# ❌ Wrong — these files no longer exist
from keyboards.admin_kb import get_admin_dashboard_kb
from keyboards.client_kb import get_offer_actions_kb
```

When adding a new keyboard, add a `@staticmethod` method to `KeyboardFactory` in `keyboards/factory.py`.

---

## 4. Logging — `structlog` Only

```python
# ✅ Correct
import structlog
logger = structlog.get_logger(__name__)
logger.info("Action happened", user_id=123, project_id=456)

# ❌ Wrong — do NOT use stdlib logging in handlers
import logging
logger = logging.getLogger(__name__)
```

Use structured key-value pairs, not f-strings:
```python
# ✅ Good
logger.error("Payment failed", payment_id=pid, error=str(e))

# ❌ Bad
logger.error(f"Payment {pid} failed: {e}")
```

---

## 5. Project Architecture

```
svu_helper/
├── handlers/           # Thin controllers — delegate to services
│   ├── common.py       # /start, /help, /cancel, calendar
│   ├── admin_routes/   # Admin-only handlers
│   └── client_routes/  # Student handlers
├── application/        # Service layer (business logic)
├── services/           # Domain services (TicketService)
├── domain/             # Entities, enums, value objects
├── infrastructure/     # Repositories (MongoDB), storage
├── keyboards/          # KeyboardFactory + callbacks
├── middlewares/        # Error handling, throttling, DI
├── utils/              # Helpers, formatters, pagination, i18n
├── locales/            # ar.json (all user-facing text)
├── config.py           # Settings from .env (pydantic-settings)
└── main.py             # Entry point
```

### Layer Rules
- **Handlers** are thin: extract data from the message, call a service, send a response.
- **Services** contain business logic and validation.
- **Repositories** handle all database I/O (MongoDB via Motor).
- **Handlers never import repositories directly** — they receive them via DI middleware.

---

## 6. Callbacks & FSM States

### Callback Data
All callback data uses typed classes from `keyboards/callbacks.py`:
```python
from keyboards.callbacks import ProjectCallback, ProjectAction
# Use: ProjectCallback(action=ProjectAction.manage, id=proj_id).pack()
```

Available callback types: `MenuCallback`, `ProjectCallback`, `PaymentCallback`, `TicketCallback`, `PageCallback`.

### FSM States
Defined in `states.py`:
- `ProjectOrder` — student project submission flow
- `AdminStates` — admin offer/broadcast/finish flows
- `TicketStates` — support ticket flows

---

## 7. Date Handling

Always use the shared helpers for dates:

```python
# Formatting dates for display:
from utils.formatters import format_datetime
display = format_datetime(some_datetime)            # "04/21 17:30"
display = format_datetime(some_datetime, "%Y-%m-%d") # "2026-04-21"

# Parsing user-input dates:
from domain.entities import _parse_deadline
valid_date = _parse_deadline(user_text)  # Raises ValueError with Arabic message
```

**NEVER** write inline `hasattr(x, "strftime")` blocks.

---

## 8. Configuration

All settings come from `config.py` (pydantic-settings, reads `.env`):
```python
from config import settings
settings.admin_ids      # List[int]
settings.BOT_TOKEN      # str
settings.MONGODB_URL    # str
```

**Never read `os.environ` directly** in handler or service code.

---

## 9. Checklist Before Submitting Code

- [ ] All user-facing text is in `locales/ar.json` + `utils/constants.py`
- [ ] Using `KeyboardFactory` for all keyboards (not shim modules)
- [ ] Using `structlog` for logging (not `import logging`)
- [ ] Using shared helpers from `utils/helpers.py` for media extraction
- [ ] Using `format_datetime()` for any date display
- [ ] Using `extract_message_content()` for parsing incoming messages
- [ ] Using `notify_admins()` for broadcasting to admin IDs
- [ ] Using `build_ticket_service()` for ticket service construction
- [ ] No duplicate helper functions defined locally in handlers
- [ ] Services receive repos via DI — handlers don't construct repos
