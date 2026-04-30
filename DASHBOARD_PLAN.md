# Observability & Admin Dashboard — Implementation Plan

## Architecture Decision

The dashboard is built as **two separate services** from the Telegram bot:

| Service | Technology | Purpose |
|---------|-----------|---------|
| `dashboard_api/` | FastAPI + Python | REST API that reads from MongoDB |
| `dashboard_ui/` | React (Vite) + Tailwind CSS | Single-page admin frontend |

Both services run alongside the bot via `docker-compose.yml`.
Authentication uses **JWT tokens** (not Basic Auth).
All prices are stored as **integers (Syrian Pounds)** — no string parsing in the dashboard.

---

## Progress Status

### ✅ Phase 1: Data Cleanup & Model Updates — COMPLETE

**Goal:** Enforce integer-only prices across the entire codebase.

**What was done:**

| File | Change |
|------|--------|
| `domain/entities.py` | `price: Optional[str]` → `price: Optional[int]` |
| `infrastructure/repositories/project.py` | `update_offer(price: str)` → `update_offer(price: int)` |
| `handlers/admin_routes/offers.py` | Admin price input is now parsed via `re.sub(r'[^\d]', '', text)` → stored as `int`. Invalid (non-numeric) input is rejected immediately. |
| `handlers/client_routes/views.py` | `str(res["price"])` added before `escape_md()` to safely format int price for Markdown |
| `scripts/migrate_prices.py` | One-time migration script ready. Converts string prices to int, hard-deletes unparseable records. Connection verified working against Atlas. |

**Migration result:** `migrated=0, deleted=0, skipped=0` — Atlas projects collection is currently empty (all test data was created after this fix was applied). The script is ready to run on future legacy data if needed.

---

### ✅ Phase 2: FastAPI Backend Setup & JWT Auth — COMPLETE

**Goal:** Create the separate API service with a secure login endpoint.

**Tasks:**
1. **`docker-compose.yml`** — Add `dashboard-api` service (Python/FastAPI container) alongside the bot.
2. **`dashboard_api/__init__.py`** — Empty init file.
3. **`dashboard_api/main.py`** — Initialize FastAPI app, configure CORS for the React frontend origin.
4. **`dashboard_api/auth.py`** — Implement:
   - `POST /api/login` endpoint accepting `username` + `password`.
   - Validates against `settings.DASHBOARD_USER` and `settings.DASHBOARD_PASS` (to be added to `config.py` and `.env`).
   - Returns a signed JWT token on success.
   - `get_current_user` dependency to protect all stat endpoints.
5. **`config.py`** — Add `DASHBOARD_USER: str` and `DASHBOARD_PASS: str` fields.
6. **`.env`** — Add `DASHBOARD_USER=admin` and `DASHBOARD_PASS=<strong_password>` values.
7. **`requirements.txt`** — Add `fastapi`, `uvicorn`, `python-jose[cryptography]`, `passlib[bcrypt]`.

**Testing Checkpoint 2:**
- Start the FastAPI service locally.
- Send `POST /api/login` with correct credentials → expect a JWT token in response.
- Send `POST /api/login` with wrong credentials → expect `401 Unauthorized`.

---

### ✅ Phase 3: Backend Aggregation Services — COMPLETE

**Goal:** Expose MongoDB stats through secure REST endpoints.

**Tasks:**
1. **`dashboard_api/services/stats.py`** — Write MongoDB aggregation pipelines:
   - **Project volume by day** — count of projects grouped by `created_at` date.
   - **Conversion rates** — count per `status` field (Pending, Offered, Accepted, Finished, Denied).
   - **Revenue over time** — sum of `price` (integer, SP) for `FINISHED` + `ACCEPTED` projects, grouped by date.
2. **`dashboard_api/routes.py`** — Create JWT-protected endpoints:
   - `GET /api/stats/overview` — returns all 3 aggregations as JSON.

**Testing Checkpoint 3:**
- Authenticate via `/api/login` to get token.
- Call `GET /api/stats/overview` with `Authorization: Bearer <token>` header.
- Verify JSON response accurately reflects the database state.

---

### ✅ Phase 4: Frontend Scaffolding & Login — COMPLETE

**Goal:** Create the React application and implement the login flow.

**Tasks:**
1. **`dashboard_ui/`** — Initialize a Vite + React project: `npm create vite@latest dashboard_ui -- --template react`.
2. **Install dependencies:** `tailwindcss`, `axios`, `react-router-dom`.
3. **Configure Tailwind CSS** in the project.
4. **`LoginPage` component** — A polished login screen that:
   - POSTs credentials to `POST /api/login`.
   - Stores the JWT in `localStorage`.
   - Redirects to the dashboard on success.
   - Shows an error message on failure.
5. **Protected route** — Redirect unauthenticated users to `/login`.

**Testing Checkpoint 4:**
- Run `npm run dev`.
- Open the browser, submit correct credentials → redirected to dashboard.
- Submit wrong credentials → error message shown.

---

### ✅ Phase 5: Frontend Dashboard UI — COMPLETE

**Goal:** Visualize live data with modern charts.

**Tasks:**
1. **Install:** `recharts` for charts.
2. **Layout component** — Persistent sidebar with navigation + top header showing logged-in admin name.
3. **Dashboard page** — Fetches from `GET /api/stats/overview` (with JWT), renders:
   - **Stat Cards:** Total Revenue (SP), Total Projects, Conversion Rate (%).
   - **Revenue Chart:** `recharts` AreaChart — revenue over time.
   - **Project Volume Chart:** LineChart — new projects per day/week.
   - **Status Breakdown:** PieChart / RadialBarChart — project status distribution.
4. **Logout button** — Clears JWT from `localStorage` and redirects to `/login`.

**Testing Checkpoint 5:**
- Log in through the UI.
- Verify all charts render with live data from the FastAPI backend.
- Verify logout clears the session.

---

## Key Decisions Already Made

| Decision | Choice | Reason |
|----------|--------|--------|
| Deployment | Single Railway service (`nixpacks.toml`) | FastAPI serves both API + built React SPA |
| Auth | JWT | Industry standard, scalable, supports future roles |
| Frontend | React + Tailwind | Scalable, easy feature additions |
| Charts | Recharts | React-native, no CDN dependency |
| Price unit | Syrian Pounds (SP) as `int` | Clean, no parsing needed at dashboard level |

---

## Railway Deployment

**How it works:** `nixpacks.toml` runs `npm run build` in `dashboard_ui/`, then starts `uvicorn`. FastAPI detects `dashboard_ui/dist/` and serves it as static files + SPA fallback.

**Required Railway environment variables:**

| Variable | Required | Description |
|----------|----------|-------------|
| `MONGO_URI` | ✅ | Atlas connection string |
| `DASHBOARD_USER` | ✅ | Admin login username |
| `DASHBOARD_PASS` | ✅ | Admin login password |
| `JWT_SECRET_KEY` | ✅ | Secret for JWTs (use `openssl rand -hex 32`) |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | ➖ | Default: 1440 (24h) |
| `DASHBOARD_CORS_ORIGIN` | ➖ | Optional when API and UI share the same Railway domain |

---

## Local Development

1. Start API: `python -m uvicorn dashboard_api.main:app --host 0.0.0.0 --port 8000 --reload`
2. Start UI: `cd dashboard_ui && npm run dev`
3. Open `http://localhost:5173` — Vite proxies `/api/*` → `localhost:8000`
4. Add to `.env`: `DASHBOARD_USER=admin`, `DASHBOARD_PASS=admin`, `JWT_SECRET_KEY=<any-secret>`

