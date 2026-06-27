import asyncio
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

# ── Env setup (must happen before importing backup modules) ───────────────────
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

_BASE_ENV = {
    "MONGO_URI": "mongodb://admin:secret@localhost:27017/?authSource=admin",
    "DB_NAME": "test_db",
    "BOT_TOKEN": "1234567890:AATEST_TOKEN",
    "ADMIN_IDS": "111,222",
}

for k, v in _BASE_ENV.items():
    os.environ.setdefault(k, v)

from backup.config import BackupSettings
from backup.runner import _human_size, run_backup


@pytest.fixture
def backup_settings() -> BackupSettings:
    """Provides a valid BackupSettings instance using the base environment."""
    with patch.dict(os.environ, _BASE_ENV, clear=False):
        return BackupSettings()


from unittest.mock import AsyncMock, MagicMock, patch

@pytest.fixture
def mock_process_ok():
    """Mocks an asyncio.create_subprocess_exec return object (success code 0)."""
    proc = MagicMock()
    proc.communicate = AsyncMock(return_value=(b"stdout", b"stderr"))
    proc.returncode = 0
    return proc


@pytest.fixture
def mock_process_fail():
    """Mocks an asyncio.create_subprocess_exec return object (fail code 1)."""
    proc = MagicMock()
    proc.communicate = AsyncMock(return_value=(b"", b"error message"))
    proc.returncode = 1
    return proc


class TestBackupSettings:
    def test_loads_required_fields(self):
        """All required env vars are read correctly."""
        with patch.dict(os.environ, _BASE_ENV, clear=False):
            s = BackupSettings()
            assert s.MONGO_URI == "mongodb://admin:secret@localhost:27017/?authSource=admin"
            assert s.DB_NAME == "test_db"
            assert s.BOT_TOKEN == "1234567890:AATEST_TOKEN"

    def test_default_interval(self):
        """BACKUP_INTERVAL_HOURS has correct default."""
        with patch.dict(os.environ, _BASE_ENV, clear=False):
            s = BackupSettings()
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


class TestHumanSize:
    def test_human_size_formatting(self, tmp_path: Path):
        """Tests the file size formatter with different byte sizes."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"a" * 500)
        assert _human_size(test_file) == "500.0 B"

        test_file.write_bytes(b"a" * 1500)
        assert _human_size(test_file) == "1.5 KB"

        test_file.write_bytes(b"a" * int(2.5 * 1024 * 1024))
        assert _human_size(test_file) == "2.5 MB"

    def test_human_size_nonexistent_file(self, tmp_path: Path):
        """If file doesn't exist, it should return 0 B."""
        assert _human_size(tmp_path / "does_not_exist.txt") == "0 B"


class TestRunBackup:
    @pytest.mark.asyncio
    async def test_success_flow_calls_all_steps(
        self, backup_settings: BackupSettings, mock_process_ok, tmp_path: Path
    ):
        """
        Happy path: mongodump -> tar -> notify admins -> cleanup.
        All steps are called in order and temp files are cleaned up.
        """
        with (
            patch("asyncio.create_subprocess_exec", return_value=mock_process_ok),
            patch("backup.runner._notify_admins") as mock_notify,
            patch("tempfile.mkdtemp", return_value=str(tmp_path)),
            patch("shutil.rmtree") as mock_rmtree,
        ):
            await run_backup(backup_settings)

        mock_notify.assert_called_once()
        # Success notification contains the checkmark
        notif_text: str = mock_notify.call_args[1].get('text', mock_notify.call_args[0][2] if len(mock_notify.call_args[0]) > 2 else '')
        assert "Backup Successful" in notif_text
        # Document was passed
        document_path = mock_notify.call_args[1].get('document_path')
        assert document_path is not None
        
        # Temp dir is always cleaned up
        mock_rmtree.assert_called_once()

    @pytest.mark.asyncio
    async def test_mongodump_failure_sends_failure_notification(
        self, backup_settings: BackupSettings, mock_process_fail, tmp_path: Path
    ):
        """If mongodump fails, an error notification is sent and execution stops."""
        with (
            patch("asyncio.create_subprocess_exec", return_value=mock_process_fail),
            patch("backup.runner._notify_admins") as mock_notify,
            patch("tempfile.mkdtemp", return_value=str(tmp_path)),
            patch("shutil.rmtree") as mock_rmtree,
        ):
            await run_backup(backup_settings)

        mock_notify.assert_called_once()
        msg: str = mock_notify.call_args[1].get('text', mock_notify.call_args[0][2] if len(mock_notify.call_args[0]) > 2 else '')
        assert "Backup FAILED" in msg
        assert "mongodump exited with code 1" in msg
        # Temp dir is still cleaned up
        mock_rmtree.assert_called_once()

    @pytest.mark.asyncio
    async def test_finally_cleans_up_on_failure(
        self, backup_settings: BackupSettings, mock_process_ok, tmp_path: Path
    ):
        """Even if notification fails unexpectedly, cleanup runs."""
        with (
            patch("asyncio.create_subprocess_exec", return_value=mock_process_ok),
            patch("backup.runner._notify_admins", side_effect=RuntimeError("boom")),
            patch("tempfile.mkdtemp", return_value=str(tmp_path)),
            patch("shutil.rmtree") as mock_rmtree,
        ):
            with pytest.raises(RuntimeError, match="boom"):
                await run_backup(backup_settings)

        mock_rmtree.assert_called_once_with(tmp_path, ignore_errors=True)
