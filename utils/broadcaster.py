import asyncio
import structlog
from typing import List, Union

from aiogram import Bot, exceptions

logger = structlog.get_logger()

class Broadcaster:
    """
    Handles mass messaging with concurrency control and safe error handling.
    """
    def __init__(self, bot: Bot, limit: int = 25):
        self.bot = bot
        self.sem = asyncio.Semaphore(limit)

    async def send_message(self, user_id: int, text: str, _retries: int = 1) -> bool:
        """
        Sends a message to a single user with safety checks.
        Returns True if successful, False otherwise.
        Retries once on TelegramRetryAfter; gives up after that to avoid
        unbounded recursion / stack overflow under sustained flood limiting.
        """
        async with self.sem:
            try:
                await self.bot.send_message(user_id, text)
                # Sleep briefly to respect the ~30 msgs/sec global limit roughly
                # 25 tasks / 0.8s ~ 31 req/s
                await asyncio.sleep(0.8)
                return True
            except exceptions.TelegramRetryAfter as e:
                if _retries <= 0:
                    logger.warning("Flood limit exceeded, skipping user", user_id=user_id)
                    return False
                logger.warning("Flood limit exceeded, retrying", sleep_seconds=e.retry_after)
                await asyncio.sleep(e.retry_after)
                return await self.send_message(user_id, text, _retries=_retries - 1)
            except Exception as e:
                logger.error("Failed to send broadcast", user_id=user_id, error=str(e))
                return False

    async def broadcast(self, user_ids: List[int], text: str) -> int:
        """
        Broadcasts the text to all user_ids.
        Returns the count of successfully sent messages.
        """
        tasks = [self.send_message(uid, text) for uid in user_ids]
        results = await asyncio.gather(*tasks)
        return results.count(True)
