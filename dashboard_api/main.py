import structlog
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from config import settings
from dashboard_api.auth import Token, verify_password, create_access_token, get_current_user

logger = structlog.get_logger(__name__)

app = FastAPI(
    title="SVU Helper Dashboard API",
    description="API for the SVU Helper Admin Dashboard",
    version="1.0.0"
)

# Allow CORS for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, this should be the specific domain of the React app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/api/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    if form_data.username != settings.DASHBOARD_USER or not verify_password(form_data.password, settings.DASHBOARD_PASS):
        logger.warning("Failed login attempt", username=form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": form_data.username})
    logger.info("Successful login", username=form_data.username)
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/login/json", response_model=Token)
async def login_json(credentials: LoginRequest):
    """
    Alternative JSON-based login for simpler frontend clients if they don't want to use URL encoded forms.
    """
    if credentials.username != settings.DASHBOARD_USER or not verify_password(credentials.password, settings.DASHBOARD_PASS):
        logger.warning("Failed JSON login attempt", username=credentials.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": credentials.username})
    logger.info("Successful JSON login", username=credentials.username)
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/me")
async def read_users_me(current_user: str = Depends(get_current_user)):
    """
    Test endpoint to verify authentication.
    """
    return {"username": current_user, "role": "admin"}
