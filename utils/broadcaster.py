import asyncio
import logging
from typing import List, Union

from aiogram import Bot, exceptions

logger = logging.getLogger(__name__)

class Broadcaster:
    """
    Handles mass messaging with concurrency control and safe error handling.
    """
    def __init__(self, bot: Bot, limit: int = 25):
        self.bot = bot
        self.sem = asyncio.Semaphore(limit)

    async def send_message(self, user_id: int, text: str) -> bool:
        """
        Sends a message to a single user with safety checks.
        Returns True if successful, False otherwise.
        """
        async with self.sem:
            try:
                await self.bot.send_message(user_id, text)
                # Sleep briefly to respect the ~30 msgs/sec global limit roughly
                # 25 tasks / 0.8s ~ 31 req/s
                await asyncio.sleep(0.8) 
                return True
            except exceptions.TelegramRetryAfter as e:
                logger.warning(f"Flood limit exceeded. Sleeping for {e.retry_after} seconds.")
                await asyncio.sleep(e.retry_after)
                return await self.send_message(user_id, text)  # Retry once
            except (exceptions.TelegramAPIError, Exception) as e:
                logger.error(f"Failed to send to {user_id}: {e}")
                return False

    async def broadcast(self, user_ids: List[int], text: str) -> int:
        """
        Broadcasts the text to all user_ids.
        Returns the count of successfully sent messages.
        """
        tasks = [self.send_message(uid, text) for uid in user_ids]
        results = await asyncio.gather(*tasks)
        return results.count(True)
