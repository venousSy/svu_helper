import aiohttp
import structlog
from typing import Optional, Dict, Any

from config import settings
from keyboards.factory import KeyboardFactory
from utils.constants import (
    MSG_OFFER_NOTIFICATION,
    MSG_PROJECT_DENIED_CLIENT,
    MSG_WORK_FINISHED_ALERT,
)
from utils.formatters import escape_md

logger = structlog.get_logger(__name__)

class TelegramService:
    """Service to send Telegram messages via the Bot API directly."""

    def __init__(self):
        self.bot_token = settings.BOT_TOKEN
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

    async def _send_request(self, payload: Dict[str, Any]) -> None:
        """Sends an HTTP POST request to the Telegram Bot API."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, json=payload) as response:
                    if response.status != 200:
                        resp_text = await response.text()
                        logger.error("Failed to send Telegram message", status=response.status, response=resp_text)
                    else:
                        logger.info("Telegram message sent successfully", chat_id=payload.get("chat_id"))
        except Exception as e:
            logger.error("Exception while sending Telegram message", error=str(e))

    async def send_offer_notification(self, user_id: int, proj_id: int, subject: str, price: str, delivery: str, notes: str) -> None:
        """Sends an offer notification with the Accept/Deny keyboard."""
        text = MSG_OFFER_NOTIFICATION.format(
            escape_md(subject),
            escape_md(str(price)),
            escape_md(delivery),
            escape_md(notes),
        )
        
        # Build the aiogram keyboard and serialize it to a dictionary
        markup = KeyboardFactory.offer_actions(proj_id).model_dump(exclude_none=True)
        
        payload = {
            "chat_id": user_id,
            "text": text,
            "parse_mode": "Markdown",
            "reply_markup": markup,
        }
        await self._send_request(payload)

    async def send_project_denied(self, user_id: int, proj_id: int) -> None:
        """Sends a notification that the project was denied."""
        text = MSG_PROJECT_DENIED_CLIENT.format(proj_id)
        payload = {
            "chat_id": user_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        await self._send_request(payload)

    async def send_project_finished(self, user_id: int, proj_id: int, subject: str) -> None:
        """Sends a notification that the project was finished. 
        Note: The actual file attachment isn't supported here yet, but we notify the student."""
        text = MSG_WORK_FINISHED_ALERT.format(escape_md(subject), proj_id)
        payload = {
            "chat_id": user_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        await self._send_request(payload)
