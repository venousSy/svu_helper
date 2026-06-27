import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from services.ticket_service import TicketService

@pytest.fixture
def mock_ticket_repo():
    repo = AsyncMock()
    repo._db = MagicMock()
    return repo

@pytest.fixture
def mock_bot():
    bot = AsyncMock()
    topic = MagicMock()
    topic.message_thread_id = 999
    bot.create_forum_topic.return_value = topic
    return bot

@pytest.fixture
def ticket_service(mock_ticket_repo, mock_bot):
    return TicketService(mock_ticket_repo, mock_bot, forum_group_id=-100)

@pytest.mark.asyncio
async def test_open_ticket(ticket_service, mock_ticket_repo, mock_bot):
    mock_ticket_repo.create_ticket.return_value = 1
    
    with patch("services.ticket_service.AuditService") as mock_audit:
        mock_audit_instance = AsyncMock()
        mock_audit.return_value = mock_audit_instance
        
        ticket_id = await ticket_service.open_ticket(
            user_id=123, text="Hello"
        )
        assert ticket_id == 1
        
        mock_ticket_repo.create_ticket.assert_called_once_with(
            user_id=123, username=None, user_full_name=None, initial_text="Hello",
            file_id=None, file_type=None
        )
        mock_bot.create_forum_topic.assert_called_once()
        mock_ticket_repo.set_thread_id.assert_called_once_with(1, 999)
        mock_bot.send_message.assert_called_once()
        mock_audit_instance.log_event.assert_called_once()


@pytest.mark.asyncio
async def test_open_ticket_forum_fails(ticket_service, mock_ticket_repo, mock_bot):
    mock_ticket_repo.create_ticket.return_value = 1
    mock_bot.create_forum_topic.side_effect = TelegramBadRequest(method=MagicMock(), message="error")
    
    with patch("services.ticket_service.AuditService") as mock_audit:
        mock_audit_instance = AsyncMock()
        mock_audit.return_value = mock_audit_instance
        ticket_id = await ticket_service.open_ticket(user_id=123, text="Hello")
        assert ticket_id == 1
        mock_ticket_repo.set_thread_id.assert_not_called()


@pytest.mark.asyncio
async def test_user_reply(ticket_service, mock_ticket_repo, mock_bot):
    mock_ticket_repo.get_ticket_by_id.return_value = {"message_thread_id": 999}
    result = await ticket_service.user_reply(1, text="reply")
    assert result is True
    mock_ticket_repo.add_message.assert_called_once_with(1, sender="user", text="reply", file_id=None, file_type=None)
    mock_bot.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_user_reply_no_ticket(ticket_service, mock_ticket_repo):
    mock_ticket_repo.get_ticket_by_id.return_value = None
    result = await ticket_service.user_reply(1, text="reply")
    assert result is False


@pytest.mark.asyncio
async def test_admin_reply(ticket_service, mock_ticket_repo, mock_bot):
    mock_ticket_repo.get_ticket_by_thread.return_value = {"ticket_id": 1, "user_id": 123, "status": "open"}
    result = await ticket_service.admin_reply(999, text="admin reply")
    assert result is not None
    mock_ticket_repo.add_message.assert_called_once_with(1, sender="admin", text="admin reply", file_id=None, file_type=None)
    mock_bot.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_admin_reply_closed_ticket(ticket_service, mock_ticket_repo, mock_bot):
    mock_ticket_repo.get_ticket_by_thread.return_value = {"ticket_id": 1, "user_id": 123, "status": "closed"}
    result = await ticket_service.admin_reply(999, text="admin reply")
    assert result is not None
    mock_ticket_repo.add_message.assert_not_called()
    mock_bot.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_close_ticket(ticket_service, mock_ticket_repo, mock_bot):
    mock_ticket_repo.get_ticket_by_id.return_value = {"message_thread_id": 999, "user_id": 123}
    
    with patch("services.ticket_service.AuditService") as mock_audit:
        mock_audit_instance = AsyncMock()
        mock_audit.return_value = mock_audit_instance
        result = await ticket_service.close_ticket(1)
        assert result is True
        mock_ticket_repo.close_ticket.assert_called_once_with(1)
        mock_bot.close_forum_topic.assert_called_once_with(chat_id=-100, message_thread_id=999)
        mock_audit_instance.log_event.assert_called_once()


@pytest.mark.asyncio
async def test_reopen_ticket(ticket_service, mock_ticket_repo, mock_bot):
    mock_ticket_repo.get_ticket_by_id.return_value = {"message_thread_id": 999, "user_id": 123}
    result = await ticket_service.reopen_ticket(1)
    assert result is True
    mock_ticket_repo.reopen_ticket.assert_called_once_with(1)
    mock_bot.reopen_forum_topic.assert_called_once_with(chat_id=-100, message_thread_id=999)

@pytest.mark.asyncio
async def test_dispatch_message_photo(ticket_service, mock_bot):
    await ticket_service._dispatch_message(chat_id=123, text="caption", file_id="f1", file_type="photo", header="H")
    mock_bot.send_photo.assert_called_once_with(chat_id=123, photo="f1", caption="H\n\ncaption")

@pytest.mark.asyncio
async def test_dispatch_message_doc(ticket_service, mock_bot):
    await ticket_service._dispatch_message(chat_id=123, text="caption", file_id="f1", file_type="document", header="H")
    mock_bot.send_document.assert_called_once_with(chat_id=123, document="f1", caption="H\n\ncaption")

@pytest.mark.asyncio
async def test_dispatch_message_video(ticket_service, mock_bot):
    await ticket_service._dispatch_message(chat_id=123, text="caption", file_id="f1", file_type="video", header="H")
    mock_bot.send_video.assert_called_once_with(chat_id=123, video="f1", caption="H\n\ncaption")

@pytest.mark.asyncio
async def test_dispatch_message_unknown(ticket_service, mock_bot):
    await ticket_service._dispatch_message(chat_id=123, text="caption", file_id="f1", file_type="unknown", header="H")
    mock_bot.send_document.assert_called_once_with(chat_id=123, document="f1", caption="H\n\ncaption")

@pytest.mark.asyncio
async def test_send_to_user_forbidden(ticket_service, mock_bot):
    mock_bot.send_message.side_effect = TelegramForbiddenError(method=MagicMock(), message="forbidden")
    with patch("services.ticket_service.logger.warning") as mock_logger:
        await ticket_service._send_to_user(123, "text", None, None)
        mock_logger.assert_called_once()
        assert "User blocked the bot" in mock_logger.call_args[0][0]

@pytest.mark.asyncio
async def test_send_to_user_exception(ticket_service, mock_bot):
    mock_bot.send_message.side_effect = Exception("General error")
    with patch("services.ticket_service.logger.error") as mock_logger:
        await ticket_service._send_to_user(123, "text", None, None)
        mock_logger.assert_called_once()

@pytest.mark.asyncio
async def test_create_forum_topic_forbidden(ticket_service, mock_bot):
    mock_bot.create_forum_topic.side_effect = TelegramForbiddenError(method=MagicMock(), message="forbidden")
    result = await ticket_service._create_forum_topic(1, 1)
    assert result is None

@pytest.mark.asyncio
async def test_send_to_topic_exception(ticket_service, mock_bot):
    mock_bot.send_message.side_effect = Exception("error")
    with patch("services.ticket_service.logger.error") as mock_logger:
        await ticket_service._send_to_topic(999, "text", None, None)
        mock_logger.assert_called_once()

@pytest.mark.asyncio
async def test_admin_reply_closed_warning_fails(ticket_service, mock_ticket_repo, mock_bot):
    mock_ticket_repo.get_ticket_by_thread.return_value = {"ticket_id": 1, "user_id": 123, "status": "closed"}
    mock_bot.send_message.side_effect = Exception("error")
    result = await ticket_service.admin_reply(999, text="admin reply")
    assert result is not None

@pytest.mark.asyncio
async def test_close_ticket_exceptions(ticket_service, mock_ticket_repo, mock_bot):
    mock_ticket_repo.get_ticket_by_id.return_value = {"message_thread_id": 999, "user_id": 123}
    with patch("services.ticket_service.AuditService") as mock_audit:
        mock_audit_instance = AsyncMock()
        mock_audit.return_value = mock_audit_instance
        
        mock_bot.close_forum_topic.side_effect = TelegramBadRequest(method=MagicMock(), message="bad")
        await ticket_service.close_ticket(1)
        
        mock_bot.close_forum_topic.side_effect = Exception("error")
        await ticket_service.close_ticket(1)
        
        mock_ticket_repo.get_ticket_by_id.return_value = None
        assert await ticket_service.close_ticket(1) is False

@pytest.mark.asyncio
async def test_admin_reply_no_ticket(ticket_service, mock_ticket_repo):
    mock_ticket_repo.get_ticket_by_thread.return_value = None
    assert await ticket_service.admin_reply(999, text="t") is None

@pytest.mark.asyncio
async def test_send_to_topic_no_forum_id(ticket_service, mock_bot):
    ticket_service._forum_group_id = None
    await ticket_service._send_to_topic(999, "t", None, None)
    mock_bot.send_message.assert_not_called()

@pytest.mark.asyncio
async def test_reopen_ticket_exceptions(ticket_service, mock_ticket_repo, mock_bot):
    mock_ticket_repo.get_ticket_by_id.return_value = {"message_thread_id": 999, "user_id": 123}
    mock_bot.reopen_forum_topic.side_effect = TelegramBadRequest(method=MagicMock(), message="bad")
    await ticket_service.reopen_ticket(1)
    
    mock_bot.reopen_forum_topic.side_effect = Exception("error")
    await ticket_service.reopen_ticket(1)
    
    mock_ticket_repo.get_ticket_by_id.return_value = None
    assert await ticket_service.reopen_ticket(1) is False

@pytest.mark.asyncio
async def test_read_helpers(ticket_service, mock_ticket_repo):
    await ticket_service.get_user_active_tickets(1)
    mock_ticket_repo.get_active_tickets.assert_called_once_with(1)
    
    await ticket_service.get_all_active_tickets()
    mock_ticket_repo.get_all_active_tickets.assert_called_once_with(0, 5)
    
    await ticket_service.get_user_closed_tickets(1)
    mock_ticket_repo.get_closed_tickets.assert_called_once_with(1)
    
    await ticket_service.get_conversation_history(1)
    mock_ticket_repo.get_recent_messages.assert_called_once_with(1, page=0, page_size=10)
    
    await ticket_service.get_message_count(1)
    mock_ticket_repo.get_message_count.assert_called_once_with(1)
    
    await ticket_service.get_ticket(1)
    mock_ticket_repo.get_ticket_by_id.assert_called_once_with(1)
