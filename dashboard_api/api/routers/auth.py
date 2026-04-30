import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from config import settings
from dashboard_api.schemas.auth import Token, LoginRequest
from dashboard_api.core.security import verify_password, create_access_token
from dashboard_api.api.dependencies import get_current_user

logger = structlog.get_logger(__name__)

router = APIRouter(
    prefix="/api/auth",
    tags=["auth"]
)

@router.post("/login", response_model=Token)
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

@router.post("/login/json", response_model=Token)
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

@router.get("/me")
async def read_users_me(current_user: str = Depends(get_current_user)):
    """
    Test endpoint to verify authentication.
    """
    return {"username": current_user, "role": "admin"}
