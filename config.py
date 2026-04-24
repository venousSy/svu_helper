
import logging
import sys
from typing import List, Optional
import functools

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import structlog

# Initialize logging for the config loader
logger = structlog.get_logger()

class Settings(BaseSettings):
    # Bot Configuration
    BOT_TOKEN: str = Field(..., description="Telegram Bot Token")
    
    # Admin Configuration
    # We read as string to handle comma-separated values safely
    ADMIN_IDS_RAW: str = Field(..., alias="ADMIN_IDS", description="List of Admin IDs (comma-separated)")
    
    # Database Configuration
    MONGO_URI: str = Field(..., description="MongoDB Connection URI")
    DB_NAME: str = Field(default="svu_helper_bot", description="Database Name")
    
    # Sentry Configuration
    SENTRY_DSN: Optional[str] = Field(default=None, description="Sentry DSN for error tracking")

    # Ticket System Configuration
    ADMIN_FORUM_GROUP_ID: Optional[int] = Field(
        default=None,
        description="Telegram Forum Supergroup ID for support tickets"
    )
    
    # Gemini AI Configuration
    GEMINI_API_KEY: Optional[str] = Field(default=None, description="Google Gemini API key for AI date parsing")

    # Logging Configuration
    LOG_FILE: str = Field(default="bot.log", description="Log file path")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @functools.cached_property
    def admin_ids(self) -> List[int]:
        """Parses the comma-separated ADMIN_IDS string into a list of integers."""
        try:
            return [int(x.strip()) for x in self.ADMIN_IDS_RAW.split(",") if x.strip()]
        except ValueError:
            logger.error("Failed to parse ADMIN_IDS", raw_ids=self.ADMIN_IDS_RAW)
            return []

# Instantiate settings
# This will raise pydantic.ValidationError if configuration is missing
try:
    settings = Settings()
except Exception as e:
    # We log it but we re-raise so the app (or test) fails loudly but traced
    logger.critical("Configuration Error", error=str(e))
    raise
