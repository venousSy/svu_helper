import pytest
from unittest.mock import AsyncMock, patch
from backup.runner import _notify_admins, _human_size, run_backup
from pathlib import Path
import tempfile
import os

@pytest.mark.asyncio
@patch("backup.runner.aiohttp.ClientSession.post")
async def test_notify_admins(mock_post):
    mock_post.return_value.__aenter__.return_value.status = 200
    
    # Text only
    await _notify_admins("token", [1], "test")
    mock_post.assert_called_once()
    
    # With document
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"data")
        f_path = Path(f.name)
    
    try:
        mock_post.reset_mock()
        await _notify_admins("token", [1], "test", f_path)
        mock_post.assert_called_once()
    finally:
        os.unlink(f_path)
    
    # Test failures
    mock_post.return_value.__aenter__.return_value.status = 400
    mock_post.return_value.__aenter__.return_value.text = AsyncMock(return_value="err")
    await _notify_admins("token", [1], "test")
    
    mock_post.side_effect = Exception("err")
    await _notify_admins("token", [1], "test")

def test_human_size():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"a" * 1024)
        f_path = Path(f.name)
    
    try:
        size = _human_size(f_path)
        assert size == "1.0 KB"
    finally:
        os.unlink(f_path)
    
    assert _human_size(Path("does_not_exist")) == "0 B"

@pytest.mark.asyncio
@patch("backup.runner.asyncio.create_subprocess_exec")
@patch("backup.runner._notify_admins")
async def test_run_backup(mock_notify, mock_exec):
    class MockConfig:
        DB_NAME = "test"
        MONGO_URI = "uri"
        BOT_TOKEN = "tok"
        admin_id_list = [1]

    # Success
    mock_proc = AsyncMock()
    mock_proc.communicate.return_value = (b"", b"")
    mock_proc.returncode = 0
    mock_exec.return_value = mock_proc
    
    await run_backup(MockConfig())
    mock_exec.assert_called()
    mock_notify.assert_called_once()
    
    # Failure mongodump
    mock_proc.returncode = 1
    mock_notify.reset_mock()
    await run_backup(MockConfig())
    mock_notify.assert_called_once()
