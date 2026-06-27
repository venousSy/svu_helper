from unittest.mock import MagicMock

import pytest

from utils.helpers import (
    get_file_id,
    get_file_size,
    extract_message_content,
    notify_admins,
    build_ticket_service
)
from unittest.mock import patch, AsyncMock
import pytest


def test_get_file_id_document():
    message = MagicMock()
    message.document.file_id = "doc_123"
    message.photo = None

    file_id, file_type = get_file_id(message)
    assert file_id == "doc_123"
    assert file_type == "document"


def test_get_file_id_photo():
    message = MagicMock()
    message.document = None

    # Mocking a list of photos, where the last one is the largest
    photo1 = MagicMock()
    photo1.file_id = "small_123"
    photo2 = MagicMock()
    photo2.file_id = "large_123"

    message.photo = [photo1, photo2]

    file_id, file_type = get_file_id(message)
    assert file_id == "large_123"
    assert file_type == "photo"


def test_get_file_id_none():
    message = MagicMock()
    message.document = None
    message.photo = None
    message.video = None
    message.audio = None
    message.voice = None

    file_id, file_type = get_file_id(message)
    assert file_id is None
    assert file_type is None


def test_get_file_id_video():
    message = MagicMock()
    message.document = None
    message.photo = None
    message.video.file_id = "video_123"
    assert get_file_id(message) == ("video_123", "video")


def test_get_file_id_audio():
    message = MagicMock()
    message.document = None
    message.photo = None
    message.video = None
    message.audio.file_id = "audio_123"
    assert get_file_id(message) == ("audio_123", "audio")


def test_get_file_id_voice():
    message = MagicMock()
    message.document = None
    message.photo = None
    message.video = None
    message.audio = None
    message.voice.file_id = "voice_123"
    assert get_file_id(message) == ("voice_123", "voice")


def test_get_file_size():
    message = MagicMock()
    message.document.file_size = 100
    message.photo = None
    message.video = None
    message.audio = None
    message.voice = None
    assert get_file_size(message) == 100
    
    message.document = None
    photo = MagicMock()
    photo.file_size = 200
    message.photo = [photo]
    assert get_file_size(message) == 200
    
    message.photo = None
    message.video = MagicMock()
    message.video.file_size = 300
    assert get_file_size(message) == 300

    message.video = None
    message.audio = MagicMock()
    message.audio.file_size = 400
    assert get_file_size(message) == 400
    
    message.audio = None
    message.voice = MagicMock()
    message.voice.file_size = 500
    assert get_file_size(message) == 500
    
    message.voice = None
    assert get_file_size(message) is None


def test_extract_message_content():
    message = MagicMock()
    message.document.file_id = "doc_123"
    message.photo = None
    message.caption = "Test Caption"
    assert extract_message_content(message) == ("Test Caption", "doc_123", "document")
    
    message.document = None
    message.text = "Test Text"
    message.video = None
    message.audio = None
    message.voice = None
    assert extract_message_content(message) == ("Test Text", None, None)


@pytest.mark.asyncio
async def test_notify_admins():
    bot = AsyncMock()
    with patch("utils.helpers.settings.admin_ids", [123, 456]):
        await notify_admins(bot, "Hello", parse_mode="HTML")
        assert bot.send_message.call_count == 2
        bot.send_message.assert_any_call(chat_id=123, text="Hello", reply_markup=None, parse_mode="HTML")
        bot.send_message.assert_any_call(chat_id=456, text="Hello", reply_markup=None, parse_mode="HTML")


@pytest.mark.asyncio
async def test_notify_admins_exception():
    bot = AsyncMock()
    bot.send_message.side_effect = Exception("Test error")
    with patch("utils.helpers.settings.admin_ids", [123]), \
         patch("utils.helpers.logger.error") as mock_logger:
        await notify_admins(bot, "Hello")
        mock_logger.assert_called_once()
        args, kwargs = mock_logger.call_args
        assert "Failed to notify admin" in args[0]
        assert kwargs["admin_id"] == 123


def test_build_ticket_service():
    repo = MagicMock()
    bot = MagicMock()
    with patch("utils.helpers.settings.ADMIN_FORUM_GROUP_ID", -100123, create=True), \
         patch("services.ticket_service.TicketService") as mock_ticket_service:
        service = build_ticket_service(repo, bot)
        mock_ticket_service.assert_called_once_with(ticket_repo=repo, bot=bot, forum_group_id=-100123)
        assert service == mock_ticket_service.return_value
