import logging
from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from api.routes import router
from database.connection import init_db
from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- SECURITY SCHEME ---
# Define the expected header for the API Key
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

async def verify_api_key(api_key: str = Security(api_key_header)):
    """Validates the incoming API key against the server configuration."""
    if api_key != settings.ADMIN_API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Could not validate credentials"
        )
    return api_key

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting Admin API...")
    await init_db()
    yield
    # Shutdown
    logger.info("🛑 Shutting down Admin API...")

app = FastAPI(title="SVU Helper Admin API", lifespan=lifespan)

# CORS (Allow Frontend to connect securely)
# Determine allowed origins based on the FRONTEND_CORS_URL
origins = [
    settings.FRONTEND_CORS_URL,
    # Localhost development fallback if the explicit URL doesn't match standard local loopbacks
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

# Ensure uniqueness and strip trailing slashes for exact matching
allowed_origins = list(set([url.rstrip('/') for url in origins]))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Protect all routes by injecting the verify_api_key dependency
app.include_router(router, prefix="/api", dependencies=[Depends(verify_api_key)])

@app.get("/")
async def root():
    return {"message": "SVU Helper Admin API is running (Protected)"}
