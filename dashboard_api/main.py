import os
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from config import settings
from infrastructure.mongo_db import Database

# Import routers
from dashboard_api.api.routers.auth import router as auth_router
from dashboard_api.api.routers.stats import router as stats_router

logger = structlog.get_logger(__name__)

# Path to the built React app (relative to the project root)
_DIST_DIR = os.path.join(os.path.dirname(__file__), "..", "dashboard_ui", "dist")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Dashboard API, connecting to MongoDB...")
    await Database.connect()
    yield
    # Shutdown
    pass

app = FastAPI(
    title="SVU Helper Dashboard API",
    description="API for the SVU Helper Admin Dashboard",
    version="1.0.0",
    lifespan=lifespan
)

# CORS: allow localhost for dev, Railway domain read from settings for prod
_allowed_origins = ["http://localhost:5173", "http://localhost:3000"]
if settings.DASHBOARD_CORS_ORIGIN:
    _allowed_origins.append(settings.DASHBOARD_CORS_ORIGIN)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API Routers ────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(stats_router)

# ── Serve React SPA ───────────────────────────────────────
# Only mount static files if the dist folder exists (built React app).
# On Railway the build step runs before the container starts.
if os.path.isdir(_DIST_DIR):
    # Serve static assets (JS/CSS/images) from /assets
    app.mount("/assets", StaticFiles(directory=os.path.join(_DIST_DIR, "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        """
        SPA catch-all: for any non-API path, serve index.html
        so that react-router-dom can handle client-side routing.
        """
        index = os.path.join(_DIST_DIR, "index.html")
        return FileResponse(index)
else:
    logger.warning("React dist folder not found — frontend not served", dist_dir=_DIST_DIR)
