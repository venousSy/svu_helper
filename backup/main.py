"""
backup/main.py
==============
Entrypoint for the backup container.

Startup sequence:
  1. Load BackupSettings from environment variables
  2. Run one backup immediately — validates the full pipeline on every deploy
  3. Schedule recurring backups every BACKUP_INTERVAL_HOURS (default: 6)
  4. Keep the asyncio event loop alive
"""
import asyncio

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from backup.config import BackupSettings
from backup.runner import run_backup

logger = structlog.get_logger(__name__)


async def main() -> None:
    # ── 1. Load config ─────────────────────────────────────────────────────────
    settings = BackupSettings()
    logger.info(
        "Backup service starting",
        db=settings.DB_NAME,
        interval_hours=settings.BACKUP_INTERVAL_HOURS,
    )

    # ── 2. Run immediately on startup ──────────────────────────────────────────
    # This lets you verify the full pipeline works the moment you deploy,
    # instead of waiting up to 6 hours to discover a misconfiguration.
    logger.info("Running startup backup")
    await run_backup(settings)

    # ── 3. Schedule recurring backups ──────────────────────────────────────────
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        func=run_backup,
        trigger="interval",
        hours=settings.BACKUP_INTERVAL_HOURS,
        args=[settings],
        id="scheduled_backup",
        name="MongoDB → Telegram backup",
        misfire_grace_time=300,  # Allow up to 5-min delay before treating as missed
    )
    scheduler.start()
    logger.info(
        "Scheduler started",
        interval_hours=settings.BACKUP_INTERVAL_HOURS,
        next_run=str(scheduler.get_job("scheduled_backup").next_run_time),
    )

    # ── 4. Keep alive ──────────────────────────────────────────────────────────
    # Sleep forever — the scheduler runs its jobs in the background
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Backup service shutting down")
        scheduler.shutdown(wait=False)


if __name__ == "__main__":
    asyncio.run(main())
