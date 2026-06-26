"""
backup/runner.py
================
Core backup orchestration logic.

Flow for each backup run:
  1. Run mongodump  (non-blocking subprocess)
  2. Compress dump  to .tar.gz (non-blocking subprocess)
  3. Upload archive to Google Drive (resumable)
  4. Prune old backups from Drive (retention policy)
  5. Notify admins of success ✅ (size + timestamp)

On ANY failure:
  - Log with structlog (error + exc_info)
  - Notify admins of failure ❌ (reason)

In ALL cases (finally block):
  - Delete local dump directory and .tar.gz archive
  - This prevents disk exhaustion even when upload fails (fixes Issue #5)
"""
import asyncio
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List

import aiohttp
import structlog

from backup.config import BackupSettings
from backup import gdrive as gdrive_client

logger = structlog.get_logger(__name__)

_TELEGRAM_API_BASE = "https://api.telegram.org/bot{token}/sendMessage"


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def _notify_admins(
    bot_token: str,
    admin_ids: List[int],
    text: str,
) -> None:
    """Send a plain-text Telegram message to every admin ID via raw HTTP."""
    url = _TELEGRAM_API_BASE.format(token=bot_token)
    async with aiohttp.ClientSession() as session:
        for admin_id in admin_ids:
            try:
                await session.post(
                    url,
                    json={"chat_id": admin_id, "text": text, "parse_mode": "HTML"},
                    timeout=aiohttp.ClientTimeout(total=10),
                )
            except Exception as exc:  # noqa: BLE001
                # Best-effort notification — never let a Telegram failure crash the backup
                logger.warning("Failed to notify admin", admin_id=admin_id, error=str(exc))


def _human_size(path: Path) -> str:
    """Return a human-readable file size string (e.g. '42.3 MB')."""
    size = path.stat().st_size
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


# ─── Main backup coroutine ────────────────────────────────────────────────────

async def run_backup(settings: BackupSettings) -> None:
    """
    Execute one full backup cycle. Called both on startup and by the scheduler.

    Args:
        settings: The loaded BackupSettings instance.
    """
    started_at = datetime.now(timezone.utc)
    timestamp = started_at.strftime("%Y-%m-%d_%H-%M-%S")
    archive_name = f"svu_helper_backup_{timestamp}.tar.gz"

    # Use a temp directory scoped to this run
    tmp_dir = Path(tempfile.mkdtemp(prefix="svu_backup_"))
    dump_dir = tmp_dir / "dump"
    archive_path = tmp_dir / archive_name

    log = logger.bind(timestamp=timestamp, db=settings.DB_NAME)
    log.info("Backup started")

    try:
        # ── Step 1: mongodump ──────────────────────────────────────────────────
        log.info("Running mongodump")
        dump_proc = await asyncio.create_subprocess_exec(
            "mongodump",
            f"--uri={settings.MONGO_URI}",
            f"--db={settings.DB_NAME}",
            f"--out={dump_dir}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await dump_proc.communicate()

        if dump_proc.returncode != 0:
            raise RuntimeError(
                f"mongodump exited with code {dump_proc.returncode}: {stderr.decode().strip()}"
            )
        log.info("mongodump complete", dump_dir=str(dump_dir))

        # ── Step 2: Compress ───────────────────────────────────────────────────
        log.info("Compressing dump", archive=archive_name)
        tar_proc = await asyncio.create_subprocess_exec(
            "tar", "czf", str(archive_path), "-C", str(tmp_dir), "dump",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, tar_stderr = await tar_proc.communicate()

        if tar_proc.returncode != 0:
            raise RuntimeError(
                f"tar exited with code {tar_proc.returncode}: {tar_stderr.decode().strip()}"
            )
        file_size = _human_size(archive_path)
        log.info("Compression complete", archive=archive_name, size=file_size)

        # ── Step 3: Upload to Google Drive ─────────────────────────────────────
        log.info("Authenticating with Google Drive")
        credentials = gdrive_client.load_credentials(settings.GDRIVE_CREDENTIALS_B64)
        service: Any = gdrive_client.build_drive_service(credentials)

        drive_file_id = gdrive_client.upload_file(
            service=service,
            local_path=archive_path,
            folder_id=settings.GDRIVE_FOLDER_ID,
        )
        log.info("Drive upload complete", drive_file_id=drive_file_id)

        # ── Step 4: Prune old backups ──────────────────────────────────────────
        deleted_count = gdrive_client.cleanup_old_backups(
            service=service,
            folder_id=settings.GDRIVE_FOLDER_ID,
            retention_days=settings.BACKUP_RETENTION_DAYS,
        )
        log.info("Retention cleanup done", deleted=deleted_count, retention_days=settings.BACKUP_RETENTION_DAYS)

        # ── Step 5: Success notification ───────────────────────────────────────
        duration = (datetime.now(timezone.utc) - started_at).seconds
        success_msg = (
            "✅ <b>Backup Successful</b>\n"
            f"📦 File: <code>{archive_name}</code>\n"
            f"📁 Size: <b>{file_size}</b>\n"
            f"🕒 Time: <b>{started_at.strftime('%Y-%m-%d %H:%M UTC')}</b>\n"
            f"⏱ Duration: <b>{duration}s</b>\n"
            f"🗑 Old backups pruned: <b>{deleted_count}</b>"
        )
        await _notify_admins(settings.BOT_TOKEN, settings.admin_id_list, success_msg)
        log.info("Backup cycle complete")

    except Exception as exc:  # noqa: BLE001
        log.error("Backup FAILED", error=str(exc), exc_info=True)

        failure_msg = (
            "❌ <b>Backup FAILED</b>\n"
            f"🕒 Time: <b>{started_at.strftime('%Y-%m-%d %H:%M UTC')}</b>\n"
            f"💥 Reason: <code>{type(exc).__name__}: {exc}</code>\n\n"
            "Check Railway logs for full stack trace."
        )
        await _notify_admins(settings.BOT_TOKEN, settings.admin_id_list, failure_msg)

    finally:
        # ── Always: clean up temp files ────────────────────────────────────────
        # Fixes Issue #5: prevents disk exhaustion if upload fails mid-run
        shutil.rmtree(tmp_dir, ignore_errors=True)
        log.info("Temp files cleaned up", tmp_dir=str(tmp_dir))
