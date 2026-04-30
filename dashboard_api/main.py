import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from infrastructure.mongo_db import Database

# Import routers
from dashboard_api.api.routers.auth import router as auth_router
from dashboard_api.api.routers.stats import router as stats_router

logger = structlog.get_logger(__name__)

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

# Allow CORS for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"], # Specific origins needed when allow_credentials=True
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(stats_router)
