import asyncio
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import aiohttp
import structlog

from backup.config import BackupSettings

log = structlog.get_logger(__name__)


async def _notify_admins(
    bot_token: str, admin_ids: list[int], text: str, document_path: Optional[Path] = None
) -> None:
    """Sends a Telegram message (and optionally a document) to all admin IDs."""
    if document_path:
        url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
    else:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    async with aiohttp.ClientSession() as session:
        for admin_id in admin_ids:
            try:
                data = aiohttp.FormData()
                data.add_field("chat_id", str(admin_id))
                data.add_field("parse_mode", "HTML")

                if document_path:
                    data.add_field("caption", text)
                    # We must open the file independently per-admin to ensure the stream is fresh
                    with document_path.open("rb") as f:
                        data.add_field("document", f, filename=document_path.name)
                        async with session.post(url, data=data) as resp:
                            if resp.status != 200:
                                resp_text = await resp.text()
                                log.warning(
                                    "Failed to notify admin with document",
                                    admin_id=admin_id,
                                    status=resp.status,
                                    text=resp_text,
                                )
                else:
                    data.add_field("text", text)
                    async with session.post(url, data=data) as resp:
                        if resp.status != 200:
                            resp_text = await resp.text()
                            log.warning(
                                "Failed to notify admin with message",
                                admin_id=admin_id,
                                status=resp.status,
                                text=resp_text,
                            )

            except Exception as e:  # noqa: BLE001
                log.warning("Admin notification exception", admin_id=admin_id, error=str(e))


def _human_size(path: Path) -> str:
    """Returns a human-readable file size (e.g., '14.2 MB')."""
    if not path.exists():
        return "0 B"
    size_bytes = path.stat().st_size
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:  # noqa: PLR2004
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


async def run_backup(settings: BackupSettings) -> None:
    """
    Core backup pipeline:
    1. Dump MongoDB using mongo-tools (mongodump).
    2. Compress the dump into a tar.gz archive.
    3. Send the archive to admins via Telegram.
    4. Clean up temporary files on disk.
    """
    structlog.contextvars.bind_contextvars(db=settings.DB_NAME)
    log.info("Backup started")

    started_at = datetime.now(timezone.utc)
    archive_name = f"svu_helper_backup_{started_at.strftime('%Y-%m-%d_%H-%M-%S')}.tar.gz"

    tmp_dir = Path(tempfile.mkdtemp(prefix="svu_backup_"))
    dump_dir = tmp_dir / "dump"
    archive_path = tmp_dir / archive_name

    try:
        # ─── Step 1: mongodump ────────────────────────────────────────────────────────
        log.info("Running mongodump")
        dump_proc = await asyncio.create_subprocess_exec(
            "mongodump", "--uri", settings.MONGO_URI, "--out", str(dump_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, dump_stderr = await dump_proc.communicate()

        if dump_proc.returncode != 0:
            raise RuntimeError(
                f"mongodump exited with code {dump_proc.returncode}: {dump_stderr.decode().strip()}"
            )
        log.info("mongodump complete", dump_dir=str(dump_dir))

        # ─── Step 2: Compress to tar.gz ───────────────────────────────────────────────
        log.info("Compressing dump", archive=archive_name)
        # -C changes directory so the tarball contains 'dump/' directly at root
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

        # ─── Step 3: Success notification with Document ───────────────────────────────
        duration = (datetime.now(timezone.utc) - started_at).seconds
        success_msg = (
            "✅ <b>Backup Successful</b>\n"
            f"📦 File: <code>{archive_name}</code>\n"
            f"📁 Size: <b>{file_size}</b>\n"
            f"🕒 Time: <b>{started_at.strftime('%Y-%m-%d %H:%M UTC')}</b>\n"
            f"⏱ Duration: <b>{duration}s</b>"
        )
        await _notify_admins(
            bot_token=settings.BOT_TOKEN,
            admin_ids=settings.admin_id_list,
            text=success_msg,
            document_path=archive_path,
        )
        log.info("Backup sent to Telegram successfully")

    except Exception as exc:  # noqa: BLE001
        log.error("Backup FAILED", error=str(exc), exc_info=True)
        failure_msg = (
            "❌ <b>Backup FAILED</b>\n"
            f"🕒 Time: <b>{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</b>\n"
            f"💥 Reason: <code>{str(exc)}</code>\n\n"
            "Check Railway logs for the full stack trace."
        )
        # Attempt to notify admins of the failure (no document)
        await _notify_admins(
            bot_token=settings.BOT_TOKEN,
            admin_ids=settings.admin_id_list,
            text=failure_msg,
        )

    finally:
        # ─── Step 4: Cleanup ──────────────────────────────────────────────────────────
        shutil.rmtree(tmp_dir, ignore_errors=True)
        structlog.contextvars.unbind_contextvars("db")
        log.info("Temp files cleaned up", tmp_dir=str(tmp_dir))
