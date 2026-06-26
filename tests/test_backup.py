"""
tests/test_backup.py
====================
Unit tests for the backup service (backup/gdrive.py + backup/runner.py + backup/config.py).

Pattern: ALL external I/O is mocked.
  - No real network calls (no Google Drive API, no Telegram API)
  - No real filesystem writes (temp dirs are mocked or use tmp_path fixture)
  - No real subprocess execution (mongodump / tar are mocked)

Run with:
    pytest tests/test_backup.py -v
"""
import asyncio
import base64
import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch, call

import pytest

# ── Env setup (must happen before importing backup modules) ───────────────────
# Set these BEFORE importing so pydantic-settings picks them up.
# We also force UTF-8 stdout encoding so structlog emoji don't crash on Windows cp1256.
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

_TEST_B64 = base64.b64encode(json.dumps({
    "type": "service_account",
    "project_id": "test-project",
    "private_key_id": "key-id",
    "private_key": "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA-----END RSA PRIVATE KEY-----\n",
    "client_email": "test@test-project.iam.gserviceaccount.com",
    "client_id": "123456789",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
}).encode()).decode()

_BASE_ENV = {
    "MONGO_URI": "mongodb://admin:secret@localhost:27017/?authSource=admin",
    "DB_NAME": "test_db",
    "BOT_TOKEN": "1234567890:AATEST_TOKEN",
    "ADMIN_IDS": "111,222",
    "GDRIVE_CREDENTIALS_B64": _TEST_B64,
    "GDRIVE_FOLDER_ID": "test_folder_id_abc123",
}

# Apply base env so module-level imports of backup.* don't fail
for k, v in _BASE_ENV.items():
    os.environ.setdefault(k, v)

from backup.config import BackupSettings
from backup import gdrive as gdrive_module
from backup.runner import _notify_admins, _human_size, run_backup


# ─────────────────────────────────────────────────────────────────────────────
# Section 1: backup/config.py
# ─────────────────────────────────────────────────────────────────────────────

class TestBackupSettings:
    def test_loads_required_fields(self):
        """All required env vars are read correctly."""
        with patch.dict(os.environ, _BASE_ENV, clear=False):
            s = BackupSettings()
            assert s.MONGO_URI == "mongodb://admin:secret@localhost:27017/?authSource=admin"
            assert s.DB_NAME == "test_db"
            assert s.BOT_TOKEN == "1234567890:AATEST_TOKEN"
            assert s.GDRIVE_FOLDER_ID == "test_folder_id_abc123"

    def test_default_retention_and_interval(self):
        """BACKUP_RETENTION_DAYS and BACKUP_INTERVAL_HOURS have correct defaults."""
        with patch.dict(os.environ, _BASE_ENV, clear=False):
            s = BackupSettings()
            assert s.BACKUP_RETENTION_DAYS == 7
            assert s.BACKUP_INTERVAL_HOURS == 6

    def test_admin_id_list_parses_correctly(self):
        """Comma-separated ADMIN_IDS string is parsed into a list of ints."""
        with patch.dict(os.environ, {**_BASE_ENV, "ADMIN_IDS": "111,222"}, clear=False):
            s = BackupSettings()
            assert s.admin_id_list == [111, 222]

    def test_admin_id_list_skips_invalid_entries(self):
        """Non-numeric values in ADMIN_IDS are silently skipped."""
        with patch.dict(os.environ, {**_BASE_ENV, "ADMIN_IDS": "111,bad,222"}, clear=False):
            s = BackupSettings()
            assert s.admin_id_list == [111, 222]


# ─────────────────────────────────────────────────────────────────────────────
# Section 2: backup/gdrive.py — load_credentials
# ─────────────────────────────────────────────────────────────────────────────

class TestLoadCredentials:
    def _make_b64(self, data: dict) -> str:
        return base64.b64encode(json.dumps(data).encode()).decode()

    def test_valid_b64_returns_credentials(self):
        """Valid base64 service account JSON returns a credentials object."""
        b64 = self._make_b64({
            "type": "service_account",
            "project_id": "proj",
            "private_key_id": "kid",
            "private_key": "-----BEGIN RSA PRIVATE KEY-----\n-----END RSA PRIVATE KEY-----\n",
            "client_email": "sa@proj.iam.gserviceaccount.com",
            "client_id": "123",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        })
        with patch("google.oauth2.service_account.Credentials.from_service_account_info") as mock_creds:
            mock_creds.return_value = MagicMock()
            result = gdrive_module.load_credentials(b64)
            mock_creds.assert_called_once()
            assert result is not None

    def test_invalid_base64_raises_value_error(self):
        """Garbage base64 input raises ValueError with a helpful message."""
        with pytest.raises(ValueError, match="not valid base64"):
            gdrive_module.load_credentials("this is not base64!!!")

    def test_valid_base64_invalid_json_raises(self):
        """Valid base64 that decodes to non-JSON raises ValueError."""
        b64 = base64.b64encode(b"not a json string").decode()
        with pytest.raises(ValueError, match="not valid JSON"):
            gdrive_module.load_credentials(b64)

    def test_wrong_account_type_raises(self):
        """JSON that is not a service_account type raises ValueError."""
        b64 = self._make_b64({"type": "authorized_user", "client_id": "id"})
        with pytest.raises(ValueError, match="not a service account"):
            gdrive_module.load_credentials(b64)


# ─────────────────────────────────────────────────────────────────────────────
# Section 3: backup/gdrive.py — upload_file
# ─────────────────────────────────────────────────────────────────────────────

class TestUploadFile:
    def test_upload_uses_resumable_true(self, tmp_path: Path):
        """upload_file always passes resumable=True to MediaFileUpload."""
        # Create a real temp file so stat() doesn't fail
        archive = tmp_path / "backup_2024-01-01.tar.gz"
        archive.write_bytes(b"fake archive content")

        mock_service = MagicMock()
        mock_request = MagicMock()
        mock_request.next_chunk.return_value = (None, {"id": "drive_file_id_xyz"})
        mock_service.files.return_value.create.return_value = mock_request

        with patch("backup.gdrive.MediaFileUpload") as mock_media:
            mock_media.return_value = MagicMock()
            gdrive_module.upload_file(mock_service, archive, folder_id="folder123")
            _, kwargs = mock_media.call_args
            assert kwargs.get("resumable") is True

    def test_upload_returns_file_id(self, tmp_path: Path):
        """upload_file returns the Drive file ID from the API response."""
        archive = tmp_path / "backup.tar.gz"
        archive.write_bytes(b"data")

        mock_service = MagicMock()
        mock_request = MagicMock()
        mock_request.next_chunk.return_value = (None, {"id": "returned_drive_id"})
        mock_service.files.return_value.create.return_value = mock_request

        with patch("backup.gdrive.MediaFileUpload"):
            result = gdrive_module.upload_file(mock_service, archive, folder_id="folder123")

        assert result == "returned_drive_id"


# ─────────────────────────────────────────────────────────────────────────────
# Section 4: backup/gdrive.py — cleanup_old_backups
# ─────────────────────────────────────────────────────────────────────────────

class TestCleanupOldBackups:
    def _make_file_entry(self, name: str, days_old: int) -> dict:
        created = datetime.now(timezone.utc) - timedelta(days=days_old)
        return {
            "id": f"id_{name}",
            "name": name,
            "createdTime": created.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        }

    def test_deletes_files_older_than_retention(self):
        """Files older than retention_days are deleted; recent ones are kept."""
        mock_service = MagicMock()
        mock_service.files.return_value.list.return_value.execute.return_value = {
            "files": [
                self._make_file_entry("old_backup.tar.gz", days_old=10),   # should delete
                self._make_file_entry("old_backup2.tar.gz", days_old=8),   # should delete
                self._make_file_entry("recent_backup.tar.gz", days_old=3), # should keep
            ]
        }

        deleted = gdrive_module.cleanup_old_backups(mock_service, "folder_id", retention_days=7)

        assert deleted == 2
        assert mock_service.files.return_value.delete.call_count == 2

    def test_skips_all_files_within_retention(self):
        """When all backups are within retention window, nothing is deleted."""
        mock_service = MagicMock()
        mock_service.files.return_value.list.return_value.execute.return_value = {
            "files": [
                self._make_file_entry("backup1.tar.gz", days_old=1),
                self._make_file_entry("backup2.tar.gz", days_old=2),
            ]
        }

        deleted = gdrive_module.cleanup_old_backups(mock_service, "folder_id", retention_days=7)

        assert deleted == 0
        mock_service.files.return_value.delete.assert_not_called()

    def test_handles_empty_folder_gracefully(self):
        """An empty Drive folder returns 0 deleted without errors."""
        mock_service = MagicMock()
        mock_service.files.return_value.list.return_value.execute.return_value = {"files": []}

        deleted = gdrive_module.cleanup_old_backups(mock_service, "folder_id", retention_days=7)

        assert deleted == 0


# ─────────────────────────────────────────────────────────────────────────────
# Section 5: backup/runner.py — helpers
# ─────────────────────────────────────────────────────────────────────────────

class TestHelpers:
    def test_human_size_bytes(self, tmp_path: Path):
        f = tmp_path / "tiny.bin"
        f.write_bytes(b"x" * 500)
        assert "B" in _human_size(f)

    def test_human_size_megabytes(self, tmp_path: Path):
        f = tmp_path / "medium.bin"
        f.write_bytes(b"x" * (3 * 1024 * 1024))  # 3 MB
        assert "MB" in _human_size(f)


# ─────────────────────────────────────────────────────────────────────────────
# Section 6: backup/runner.py — run_backup()
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def backup_settings() -> BackupSettings:
    return BackupSettings()


@pytest.fixture
def mock_process_ok():
    """Returns a mock asyncio.Process with returncode=0."""
    proc = AsyncMock()
    proc.returncode = 0
    proc.communicate = AsyncMock(return_value=(b"", b""))
    return proc


@pytest.fixture
def mock_process_fail():
    """Returns a mock asyncio.Process with returncode=1 (failure)."""
    proc = AsyncMock()
    proc.returncode = 1
    proc.communicate = AsyncMock(return_value=(b"", b"mongodump: auth failed"))
    return proc


class TestRunBackup:
    @pytest.mark.asyncio
    async def test_success_flow_calls_all_steps(
        self, backup_settings: BackupSettings, mock_process_ok, tmp_path: Path
    ):
        """
        Happy path: mongodump -> tar -> upload -> cleanup -> success notify.
        All steps are called in order and temp files are cleaned up.
        """
        # Create the archive file that _human_size() will stat()
        fake_archive = tmp_path / f"svu_helper_backup_{datetime.now(timezone.utc).strftime('%Y-%m-%d_%H-%M-%S')}.tar.gz"
        fake_archive.write_bytes(b"x" * 1024)

        with (
            patch("asyncio.create_subprocess_exec", return_value=mock_process_ok),
            patch("backup.runner.gdrive_client.load_credentials", return_value=MagicMock()),
            patch("backup.runner.gdrive_client.build_drive_service", return_value=MagicMock()),
            patch("backup.runner.gdrive_client.upload_file", return_value="drive_id_123") as mock_upload,
            patch("backup.runner.gdrive_client.cleanup_old_backups", return_value=1) as mock_cleanup,
            patch("backup.runner._notify_admins") as mock_notify,
            patch("tempfile.mkdtemp", return_value=str(tmp_path)),
            patch("shutil.rmtree") as mock_rmtree,
        ):
            await run_backup(backup_settings)

        mock_upload.assert_called_once()
        mock_cleanup.assert_called_once()
        mock_notify.assert_called_once()
        # Success notification contains the checkmark
        notif_text: str = mock_notify.call_args[0][2]
        assert "Backup Successful" in notif_text
        # Temp dir is always cleaned up
        mock_rmtree.assert_called_once()

    @pytest.mark.asyncio
    async def test_success_notification_contains_size_and_time(
        self, backup_settings: BackupSettings, mock_process_ok, tmp_path: Path
    ):
        """Success notification message contains file size and UTC timestamp."""
        fake_archive = tmp_path / f"svu_helper_backup_{datetime.now(timezone.utc).strftime('%Y-%m-%d_%H-%M-%S')}.tar.gz"
        fake_archive.write_bytes(b"x" * (5 * 1024 * 1024))  # 5 MB

        with (
            patch("asyncio.create_subprocess_exec", return_value=mock_process_ok),
            patch("backup.runner.gdrive_client.load_credentials", return_value=MagicMock()),
            patch("backup.runner.gdrive_client.build_drive_service", return_value=MagicMock()),
            patch("backup.runner.gdrive_client.upload_file", return_value="id"),
            patch("backup.runner.gdrive_client.cleanup_old_backups", return_value=0),
            patch("backup.runner._notify_admins") as mock_notify,
            patch("tempfile.mkdtemp", return_value=str(tmp_path)),
            patch("shutil.rmtree"),
        ):
            await run_backup(backup_settings)

        msg: str = mock_notify.call_args[0][2]
        assert "MB" in msg or "KB" in msg   # file size present
        assert "UTC" in msg                  # timestamp present

    @pytest.mark.asyncio
    async def test_mongodump_failure_sends_failure_notification(
        self, backup_settings: BackupSettings, mock_process_fail, tmp_path: Path
    ):
        """A non-zero mongodump exit code triggers the ❌ failure notification."""
        with (
            patch("asyncio.create_subprocess_exec", return_value=mock_process_fail),
            patch("backup.runner._notify_admins") as mock_notify,
            patch("tempfile.mkdtemp", return_value=str(tmp_path)),
            patch("shutil.rmtree"),
        ):
            await run_backup(backup_settings)

        mock_notify.assert_called_once()
        msg: str = mock_notify.call_args[0][2]
        assert "❌" in msg

    @pytest.mark.asyncio
    async def test_upload_failure_sends_failure_notification(
        self, backup_settings: BackupSettings, mock_process_ok, tmp_path: Path
    ):
        """An exception during Drive upload triggers the failure notification."""
        fake_archive = tmp_path / f"svu_helper_backup_{datetime.now(timezone.utc).strftime('%Y-%m-%d_%H-%M-%S')}.tar.gz"
        fake_archive.write_bytes(b"data")

        with (
            patch("asyncio.create_subprocess_exec", return_value=mock_process_ok),
            patch("backup.runner.gdrive_client.load_credentials", return_value=MagicMock()),
            patch("backup.runner.gdrive_client.build_drive_service", return_value=MagicMock()),
            patch("backup.runner.gdrive_client.upload_file", side_effect=Exception("API quota exceeded")),
            patch("backup.runner._notify_admins") as mock_notify,
            patch("tempfile.mkdtemp", return_value=str(tmp_path)),
            patch("shutil.rmtree"),
        ):
            await run_backup(backup_settings)

        msg: str = mock_notify.call_args[0][2]
        assert "Backup FAILED" in msg
        assert "quota" in msg.lower()

    @pytest.mark.asyncio
    async def test_finally_cleans_up_on_upload_failure(
        self, backup_settings: BackupSettings, mock_process_ok, tmp_path: Path
    ):
        """
        Even when the upload fails, the finally block must still
        delete the local temp directory -- no disk leaks.
        """
        fake_archive = tmp_path / f"svu_helper_backup_{datetime.now(timezone.utc).strftime('%Y-%m-%d_%H-%M-%S')}.tar.gz"
        fake_archive.write_bytes(b"data")

        with (
            patch("asyncio.create_subprocess_exec", return_value=mock_process_ok),
            patch("backup.runner.gdrive_client.load_credentials", return_value=MagicMock()),
            patch("backup.runner.gdrive_client.build_drive_service", return_value=MagicMock()),
            patch("backup.runner.gdrive_client.upload_file", side_effect=RuntimeError("boom")),
            patch("backup.runner._notify_admins"),
            patch("tempfile.mkdtemp", return_value=str(tmp_path)),
            patch("shutil.rmtree") as mock_rmtree,
        ):
            await run_backup(backup_settings)

        # shutil.rmtree MUST be called even though upload raised
        mock_rmtree.assert_called_once_with(tmp_path, ignore_errors=True)
