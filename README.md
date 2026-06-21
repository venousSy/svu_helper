# SVU Helper Bot 🎓

A production-grade Telegram bot built with **Aiogram 3** that manages the full
lifecycle of student project submissions — from submission through tutor offers,
payment verification, and delivery.

---

## ✨ Features

| Feature | Details |
|---|---|
| 📚 **Project Submission** | FSM-guided multi-step flow for students; supports text, photos, and documents |
| 🎁 **Offer Management** | Admin sends price + delivery offers; student accepts or rejects |
| 💳 **Payment Verification** | Student uploads payment receipt; admin approves or rejects |
| 📂 **Project Tracking** | Paginated views: Pending, Ongoing, Finished, All (master report) |
| 🎫 **Support Tickets** | Telegram forum topic per ticket, bridging student and admin |
| 🔗 **Peer-Link Board** | Students advertise and browse peer collaboration opportunities |
| 📢 **Broadcasting** | Admin mass-sends announcements to all registered users |
| 🚨 **Urgent-Cases Monitor** | Background job alerts admins every 6 h about overdue projects |
| 📊 **REST Dashboard API** | JWT-secured FastAPI dashboard for ops/analytics |
| 🛡 **Sentry + structlog** | Structured logging; Sentry error tracking in production |

---

## 🏗 Architecture

```
svu_helper/
├── main.py                  # Entry point: bot, dispatcher, middleware stack
├── config.py                # pydantic-settings; reads .env (BOT_TOKEN, MONGO_URI, …)
├── states.py                # Aiogram FSM state groups
│
├── handlers/
│   ├── common.py            # /start, /help, /cancel, calendar picker
│   ├── admin_routes/        # Admin panel: projects, offers, payments, broadcast
│   └── client_routes/       # Student flow: submit, track, respond to offers
│
├── application/             # Service layer — orchestrates business workflows
├── services/                # Domain services (TicketService, …)
├── domain/                  # Entities, enums, value objects (_parse_deadline, …)
│
├── infrastructure/
│   └── repositories/        # Async Motor (MongoDB) repositories per aggregate
│
├── database/
│   └── connection.py        # init_db(); Motor client singleton
│
├── keyboards/
│   ├── factory.py           # KeyboardFactory — all InlineKeyboardMarkup builders
│   └── callbacks.py         # Typed callback data (CallbackData subclasses)
│
├── middlewares/
│   ├── throttling.py        # Rate-limit: 1 req / 0.5 s per user (shared cache)
│   ├── db_injection.py      # Injects repo objects into handler data dict
│   ├── error_handler.py     # Catches unhandled exceptions; sends user-friendly reply
│   ├── maintenance.py       # Blocks non-admin traffic during maintenance mode
│   ├── correlation.py       # Attaches request_id to every structlog context
│   └── activity_tracker.py  # Upserts last-active timestamp for each user
│
├── utils/
│   ├── constants.py         # MSG_* / BTN_* constants loaded from locales/ar.json
│   ├── formatters.py        # format_project_list, format_datetime, escape_md, …
│   ├── helpers.py           # notify_admins, get_file_id, extract_message_content
│   ├── pagination.py        # paginate(), build_nav_keyboard()
│   ├── broadcaster.py       # Broadcaster — throttled mass-send
│   └── i18n.py              # Loads locales/ar.json at startup
│
├── locales/
│   └── ar.json              # Single source of truth for all Arabic UI text
│
├── dashboard_api/           # FastAPI REST API (JWT auth) for the ops dashboard
├── dashboard_ui/            # React/Vite frontend (served separately)
│
├── scripts/                 # One-off maintenance / dev utilities
│   ├── wipe_db.py           # ⚠️ Drop core collections (requires typed confirmation)
│   ├── read_db.py           # Print current DB records
│   ├── debug_commands.py    # Reset bot command menu
│   └── migrate_prices.py    # Data migration helper
│
├── Dockerfile               # Bot image
├── Dockerfile.dashboard     # Dashboard API image
├── docker-compose.yml       # Full stack: bot + dashboard-api + mongo + redis + nginx
└── nixpacks.toml            # Railway deployment config
```

### Middleware execution order (per update)

```
CorrelationLogging → ActivityTracker → DbInjection → Throttling → Maintenance → ErrorHandler → Handler
```

---

## ⚙️ Configuration

All settings are read from a `.env` file via **pydantic-settings**.

```env
# Required
BOT_TOKEN=your_telegram_bot_token
ADMIN_IDS=123456789,987654321          # comma-separated
MONGO_URI=mongodb://admin:secret@localhost:27017

# Optional — sensible defaults shown
DB_NAME=svu_helper_bot
REDIS_URI=redis://localhost:6379/0     # also accepted: REDIS_URL
SENTRY_DSN=                           # leave blank to disable
ADMIN_FORUM_GROUP_ID=                 # Telegram forum supergroup for tickets
GEMINI_API_KEY=                       # AI-assisted deadline parsing

# Dashboard API (JWT auth)
DASHBOARD_USER=admin
DASHBOARD_PASS=change_me
JWT_SECRET_KEY=change_me_in_production
DASHBOARD_CORS_ORIGIN=https://your-app.up.railway.app
```

> [!IMPORTANT]
> `MONGO_URI` also accepts the aliases `MONGODB_URL` and `MONGO_URL` for
> Railway / Atlas compatibility.

---

## 🚀 Running Locally

### Prerequisites
- Python 3.11+
- MongoDB (local or Atlas)
- Redis (local or managed)

### Quick start

```bash
# 1. Clone and enter the repo
git clone <repo-url> && cd svu_helper

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy and edit the env file
cp .env.example .env              # then fill in BOT_TOKEN, ADMIN_IDS, MONGO_URI

# 5. Start the bot
python main.py
```

### Docker Compose (full stack)

```bash
# Copy and fill env values
cp .env.example .env

docker compose up --build -d
```

Services brought up: `bot`, `dashboard-api`, `mongo`, `redis`, `nginx`, `mongo-express`.

---

## 🛠 Maintenance Scripts

Run these from the project root (your venv must be active):

| Script | Purpose |
|---|---|
| `python scripts/read_db.py` | Print all records in the database |
| `python scripts/debug_commands.py` | Re-register bot command menu with BotFather |
| `python scripts/migrate_prices.py` | One-off data migration for price fields |
| `python scripts/wipe_db.py` | **⚠️ Irreversibly drop** `projects`, `payments`, `counters` (prompts for confirmation) |

---

## 🧪 Tests

```bash
pytest tests/ -v
```

---

## 📖 Developer Notes

- **Never hard-code Arabic text** in handlers or services. All user-facing strings
  live in [`locales/ar.json`](locales/ar.json) and are exposed as `MSG_*` / `BTN_*`
  constants in `utils/constants.py`.
- **Keyboards** are built exclusively through `KeyboardFactory` in
  `keyboards/factory.py`.
- **Logging** uses `structlog` with structured key-value pairs — no f-string
  messages in log calls.
- **Dates** are formatted via `format_datetime()` and parsed via `_parse_deadline()`.
- See [`AGENTS.md`](AGENTS.md) for the full coding-standards reference used by
  AI agents working on this codebase.
