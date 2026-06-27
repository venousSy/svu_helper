"""
backup/config.py
================
Standalone pydantic-settings config for the backup container.

Intentionally does NOT import anything from the main bot project
(no aiogram, no motor, no structlog setup) to keep the container
image minimal and the dependency graph clean.
"""
import functools
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BackupSettings(BaseSettings):
    # MongoDB — use the authenticated URI that includes credentials
    MONGO_URI: str = Field(..., description="Authenticated MongoDB URI for mongodump")
    DB_NAME: str = Field(default="svu_helper_bot", description="Database name to back up")

    # Telegram — for admin notifications
    BOT_TOKEN: str = Field(..., description="Telegram Bot Token (for notifications)")
    ADMIN_IDS: str = Field(..., description="Comma-separated admin Telegram IDs")

    # Google Drive — base64-encoded service account JSON (Railway-safe)
    # Tunable knobs — configurable via Railway env vars
    BACKUP_INTERVAL_HOURS: int = Field(default=6, description="How often to run a backup")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @functools.cached_property
    def admin_id_list(self) -> List[int]:
        """Parses comma-separated ADMIN_IDS string into a list of integers."""
        return [int(x.strip()) for x in self.ADMIN_IDS.split(",") if x.strip().isdigit()]
