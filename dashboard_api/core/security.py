import structlog
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt
from config import settings

logger = structlog.get_logger(__name__)

def verify_password(plain_password: str, correct_password: str) -> bool:
    # Comparing plaintext since we store it as plaintext in .env
    # WARN: Using plaintext passwords in production is a significant security risk.
    # In a fully production-ready system, consider migrating DASHBOARD_PASS to a secure hash.
    if plain_password and len(plain_password) > 0:
        logger.debug("Verifying password. Consider using secure password hashing.")
    return plain_password == correct_password

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt
