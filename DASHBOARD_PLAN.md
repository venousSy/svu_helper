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

## Planned Improvements

### ⏳ Phase 6: Architectural Compliance & UI Refactor
**Goal:** Fix technical debt by enforcing the Design Tokens rule.
- Refactor React components (like `StatCard.jsx`) to remove hardcoded Tailwind utilities (`bg-blue-500/10`, `duration-200`).
- Replace hardcoded values with semantic tokens from `tokens.css` (e.g., `bg-brand-primary/10`, `duration-normal`).

### ⏳ Phase 7: Projects List View (Read-Only)
**Goal:** Provide a granular data table of all projects.
- Create a new `/projects` page in the React frontend.
- Build a paginated Data Table component.
- Implement backend API endpoints for paginated project fetching with search (by student ID) and filtering (by status).

### ⏳ Phase 8: Project Management Capabilities (Read/Write)
**Goal:** Allow admins to manage projects directly from the web UI.
- Add action buttons to the Projects List table.
- Implement backend endpoints to update project statuses (approve/deny, set price, mark finished).
- Ensure updates sync properly with the Telegram bot's state.

### ⏳ Phase 9: Support Ticket Management
**Goal:** Manage student support tickets via the dashboard.
- Create a "Tickets" view showing open/closed tickets.
- Implement a chat interface to view ticket history and reply to users.
- Connect dashboard replies to the Telegram bot to forward messages to users.

### ⏳ Phase 10: UI/UX Polish
**Goal:** Enhance the user experience of the dashboard.
- Add loading skeletons for charts and tables during data fetches.
- Add toast notifications for successful/failed API mutations.
- Ensure the sidebar is fully collapsible and the layout is perfectly responsive on mobile devices.

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

