# Observability & Admin Dashboard Implementation Plan

This plan details the implementation of a secure web dashboard for the SVU Helper bot to visualize project volume, conversion rates, and revenue over time. 

To minimize bugs and ensure stability, the work is divided into **5 verifiable phases**. We will complete and test each phase before moving to the next.

---

## Phase 1: Data Cleanup & Model Updates
*Goal: Ensure all price data in the database is strictly integer-based (Syrian Pounds) and clean up legacy data.*

**Tasks:**
1. **[NEW] `scripts/migrate_prices.py`:** Create a script to iterate over all projects. Strip non-numeric characters from the `price` field (e.g., "150$" -> `150`). **Hard-delete** any records containing unparseable strings.
2. **[MODIFY] `domain/entities.py`:** Update the Pydantic schema for `price` to be strictly `int`.
3. **[MODIFY] Handlers:** Update payment and offer handlers (e.g., `handlers/client_routes/payment.py`, `handlers/admin_routes/offers.py`) to ensure only integers are passed to the database.
**Testing Checkpoint 1:** Run the bot locally, create a test project, and verify the price is saved as an integer. Run the migration script and verify old data is converted or deleted.

---

## Phase 2: FastAPI Backend Setup & Auth
*Goal: Create the separate backend service and secure it with JWT.*

**Tasks:**
1. **[MODIFY] `docker-compose.yml`:** Add the `dashboard-api` service.
2. **[NEW] `dashboard_api/main.py`:** Initialize the FastAPI app and configure CORS.
3. **[NEW] `dashboard_api/auth.py`:** Implement a `/api/login` endpoint that checks `DASHBOARD_USER` and `DASHBOARD_PASS` from `config.py` and issues a JSON Web Token (JWT). Create a `get_current_user` dependency.
**Testing Checkpoint 2:** Use an API client (like Postman or a simple Python script) to send a POST request to `/api/login` and verify a JWT is successfully returned.

---

## Phase 3: Backend Aggregation Services
*Goal: Build the MongoDB queries to extract statistical data.*

**Tasks:**
1. **[NEW] `dashboard_api/services/stats.py`:** Write MongoDB aggregation pipelines for:
   - Project volume over time.
   - Project conversion rates (Accepted vs Pending vs Rejected).
   - Total Revenue (sum of integer prices).
2. **[NEW] `dashboard_api/routes.py`:** Create secure endpoints (e.g., `/api/stats/overview`) protected by the JWT dependency, returning the aggregated data.
**Testing Checkpoint 3:** Make authenticated API requests to the new stats endpoints and verify the JSON data accurately reflects the database state.

---

## Phase 4: Frontend Scaffolding & Login
*Goal: Set up the React application and build the authentication flow.*

**Tasks:**
1. **[NEW] `dashboard_ui/`:** Initialize a new React project using Vite.
2. **Setup:** Install `tailwindcss`, `axios`, and `react-router-dom`. Configure Tailwind.
3. **[NEW] UI Components:** Build a sleek Login Page that accepts credentials, hits the FastAPI `/api/login` endpoint, and stores the JWT in `localStorage`.
**Testing Checkpoint 4:** Start the Vite dev server (`npm run dev`), open the browser, and successfully log in through the UI.

---

## Phase 5: Frontend Dashboard UI
*Goal: Visualize the statistical data using modern charts.*

**Tasks:**
1. **Setup:** Install `recharts` for charting.
2. **[NEW] UI Components:** 
   - Build the persistent layout (Sidebar + Header).
   - Build the Overview Dashboard fetching data from `/api/stats/overview`.
   - Create Stat Cards (Total Revenue, Total Projects).
   - Create Charts (Revenue Line/Bar Chart, Project Volume Chart, Status Doughnut Chart).
**Testing Checkpoint 5:** Log into the dashboard and verify that all charts render correctly, fetching live data from the FastAPI backend.
