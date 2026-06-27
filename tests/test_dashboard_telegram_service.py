import pytest
from unittest.mock import AsyncMock, patch
from dashboard_api.services.telegram_service import TelegramService

@pytest.fixture
def telegram_service():
    return TelegramService()

@pytest.mark.asyncio
@patch("dashboard_api.services.telegram_service.aiohttp.ClientSession.post")
async def test_send_request(mock_post, telegram_service):
    # Success
    mock_post.return_value.__aenter__.return_value.status = 200
    await telegram_service._send_request({"chat_id": 123})
    mock_post.assert_called_once()
    
    # Failure
    mock_post.reset_mock()
    mock_post.return_value.__aenter__.return_value.status = 400
    mock_post.return_value.__aenter__.return_value.text = AsyncMock(return_value="error")
    await telegram_service._send_request({"chat_id": 123})
    mock_post.assert_called_once()
    
    # Exception
    mock_post.reset_mock()
    mock_post.side_effect = Exception("error")
    await telegram_service._send_request({"chat_id": 123})

@pytest.mark.asyncio
@patch("dashboard_api.services.telegram_service.aiohttp.ClientSession.get")
async def test_get_file_url(mock_get, telegram_service):
    # Success
    mock_get.return_value.__aenter__.return_value.status = 200
    mock_get.return_value.__aenter__.return_value.json = AsyncMock(return_value={"ok": True, "result": {"file_path": "a/b.jpg"}})
    res = await telegram_service.get_file_url("fid")
    assert res.endswith("a/b.jpg")
    
    # Failure not 200
    mock_get.return_value.__aenter__.return_value.status = 400
    mock_get.return_value.__aenter__.return_value.text = AsyncMock(return_value="err")
    assert await telegram_service.get_file_url("fid") is None
    
    # Failure not ok
    mock_get.return_value.__aenter__.return_value.status = 200
    mock_get.return_value.__aenter__.return_value.json = AsyncMock(return_value={"ok": False})
    assert await telegram_service.get_file_url("fid") is None
    
    # Exception
    mock_get.side_effect = Exception("err")
    assert await telegram_service.get_file_url("fid") is None

@pytest.mark.asyncio
@patch.object(TelegramService, "_send_request")
async def test_send_notifications(mock_send, telegram_service):
    await telegram_service.send_offer_notification(1, 1, "sub", "100", "tmrw", "notes")
    mock_send.assert_called_once()
    
    mock_send.reset_mock()
    await telegram_service.send_project_denied(1, 1)
    mock_send.assert_called_once()
    
    mock_send.reset_mock()
    await telegram_service.send_project_finished(1, 1, "sub")
    mock_send.assert_called_once()
