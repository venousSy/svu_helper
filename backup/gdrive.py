"""
backup/gdrive.py
================
Google Drive client for the backup service.

Three focused responsibilities:
  1. load_credentials()  — decode base64 env var → Google credentials object
  2. upload_file()       — resumable upload (handles large files + API rate limits)
  3. cleanup_old_backups() — prune Drive folder to enforce retention policy
"""
import base64
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

import structlog
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

logger = structlog.get_logger(__name__)

# The only Drive scope we need: manage files in folders we own
_SCOPES: List[str] = ["https://www.googleapis.com/auth/drive"]


def load_credentials(b64_string: str) -> service_account.Credentials:
    """
    Decode a base64-encoded Google Service Account JSON string and return
    scoped credentials.

    Raises:
        ValueError: If the string is not valid base64 or the decoded content
                    is not valid JSON with the expected service-account fields.
    """
    try:
        raw_json = base64.b64decode(b64_string)
    except Exception as exc:
        raise ValueError(
            "GDRIVE_CREDENTIALS_B64 is not valid base64. "
            "Re-generate it with: base64 gdrive.json"
        ) from exc

    try:
        info: Dict[str, Any] = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "Decoded GDRIVE_CREDENTIALS_B64 is not valid JSON. "
            "Ensure you encoded the correct .json file."
        ) from exc

    if info.get("type") != "service_account":
        raise ValueError(
            "Decoded credentials are not a service account JSON. "
            "Download the correct key from Google Cloud Console → IAM → Service Accounts."
        )

    credentials = service_account.Credentials.from_service_account_info(
        info, scopes=_SCOPES
    )
    logger.info("Google Drive credentials loaded", client_email=info.get("client_email"))
    return credentials


def build_drive_service(credentials: service_account.Credentials) -> Any:
    """Build and return an authenticated Google Drive API service object."""
    return build("drive", "v3", credentials=credentials, cache_discovery=False)


def upload_file(
    service: Any,
    local_path: Path,
    folder_id: str,
    mime_type: str = "application/gzip",
) -> str:
    """
    Upload a local file to a Google Drive folder using a resumable upload.

    Resumable upload (resumable=True) handles:
    - Large files (no 5MB in-memory limit)
    - API rate-limit retries (the client library retries automatically)
    - Network interruptions during upload

    Returns:
        The Google Drive file ID of the uploaded file.

    Raises:
        HttpError: On unrecoverable API errors.
    """
    file_metadata = {
        "name": local_path.name,
        "parents": [folder_id],
    }
    media = MediaFileUpload(
        str(local_path),
        mimetype=mime_type,
        resumable=True,   # ← fixes Issue #6: chunked & resumable upload
        chunksize=10 * 1024 * 1024,  # 10 MB chunks
    )

    logger.info("Uploading backup to Google Drive", file=local_path.name, folder_id=folder_id)

    request = service.files().create(body=file_metadata, media_body=media, fields="id")
    response = None
    while response is None:
        _, response = request.next_chunk()

    file_id: str = response.get("id", "")
    logger.info("Upload complete", drive_file_id=file_id)
    return file_id


def cleanup_old_backups(
    service: Any,
    folder_id: str,
    retention_days: int,
) -> int:
    """
    Delete backup files from the Drive folder that are older than `retention_days`.

    Only files whose names end in `.tar.gz` are considered (to avoid
    accidentally deleting other files the user may have placed in the folder).

    Returns:
        Number of files deleted.
    """
    cutoff: datetime = datetime.now(timezone.utc) - timedelta(days=retention_days)
    deleted = 0

    try:
        results = (
            service.files()
            .list(
                q=f"'{folder_id}' in parents and name contains '.tar.gz' and trashed=false",
                fields="files(id, name, createdTime)",
                orderBy="createdTime asc",
            )
            .execute()
        )
        files: List[Dict[str, str]] = results.get("files", [])
        logger.info("Drive folder scanned", total_backup_files=len(files), retention_days=retention_days)

        for f in files:
            created_str: str = f.get("createdTime", "")
            # Drive returns ISO 8601 with Z suffix
            created_at = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
            if created_at < cutoff:
                service.files().delete(fileId=f["id"]).execute()
                logger.info("Old backup deleted from Drive", name=f["name"], created_at=created_str)
                deleted += 1

    except HttpError as exc:
        # Non-fatal: log and continue. The upload already succeeded.
        logger.warning("Failed to clean up old Drive backups", error=str(exc))

    return deleted
