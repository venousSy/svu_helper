
import pytest
from unittest.mock import AsyncMock, MagicMock
from middlewares.error_handler import GlobalErrorHandler
from aiogram.types import Message, CallbackQuery

@pytest.mark.asyncio
async def test_error_handler_catches_exception():
    # Setup
    middleware = GlobalErrorHandler()
    handler = AsyncMock(side_effect=ValueError("Test Error"))
    event = MagicMock(spec=Message)
    # Configure the mock to allow accessing nested attributes
    # or simple remove the spec restriction for the test if it's too strict for simple property access
    # Better yet, just mock the specific attribute structure needed
    user_mock = MagicMock()
    user_mock.id = 123
    event.from_user = user_mock
    event.answer = AsyncMock()
    data = {}

    # Execution
    result = await middleware(handler, event, data)

    # Verification
    # 1. Handler was called
    handler.assert_called_once()
    
    # 2. Exception caught (result is None)
    assert result is None
    
    # 3. User notified
    event.answer.assert_called_once()
    assert "حدث خطأ" in event.answer.call_args[0][0]

@pytest.mark.asyncio
async def test_error_handler_passes_success():
    # Setup
    middleware = GlobalErrorHandler()
    handler = AsyncMock(return_value="Success")
    event = MagicMock(spec=Message)
    data = {}

    # Execution
    result = await middleware(handler, event, data)

    # Verification
    assert result == "Success"
    event.answer.assert_not_called()
