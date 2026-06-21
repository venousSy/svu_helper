"""
Throttling middleware
====================
Limits each user to one request per ``rate_limit`` seconds, **across all
event types** that the same middleware instance is registered on.

Key design decisions
--------------------
* A **single** ``ThrottlingMiddleware`` instance should be reused for every
  event observer (message, callback_query, …).  ``main.py`` must pass the
  same object to each ``dp.<observer>.middleware(...)`` call so that the
  shared ``TTLCache`` is actually shared.

* Cache key is ``user_id`` alone (not per-event-type) so a spammer cannot
  bypass the message rate-limit by sending rapid callback presses instead.

* ``cachetools.TTLCache`` with ``ttl=rate_limit`` naturally expires entries
  after the window elapses — no manual timestamp comparison needed.

* The import of ``CallbackQuery`` is hoisted to module level (avoids a
  repeated import on every hot-path call).
"""
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message
import cachetools
import structlog

logger = structlog.get_logger(__name__)


class ThrottlingMiddleware(BaseMiddleware):
    """
    Anti-spam middleware.

    Rate-limits each Telegram user to one accepted request every
    ``rate_limit`` seconds.  Throttled events are silently dropped
    (returns ``None`` without calling the next handler).

    Usage in main.py
    ----------------
    Create **one** instance and register it on every observer you want
    to protect::

        throttle = ThrottlingMiddleware(rate_limit=0.5)
        dp.message.middleware(throttle)
        dp.callback_query.middleware(throttle)
    """

    def __init__(self, rate_limit: float = 2.0) -> None:
        self.rate_limit = rate_limit
        # Shared across all event types registered on this instance.
        # TTL == rate_limit means the entry lives for exactly one window.
        self._cache: cachetools.TTLCache = cachetools.TTLCache(
            maxsize=10_000, ttl=rate_limit
        )

    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: Dict[str, Any],
    ) -> Any:
        # Resolve user_id for the two primary event types we throttle.
        if isinstance(event, (Message, CallbackQuery)):
            user = event.from_user
            if user is None:
                # Anonymous channel posts — pass through untouched.
                return await handler(event, data)
            user_id: int = user.id
        else:
            # Unknown event type (e.g. inline_query) — pass through.
            return await handler(event, data)

        if user_id in self._cache:
            logger.warning(
                "Request throttled",
                user_id=user_id,
                rate_limit=self.rate_limit,
            )
            return None  # Drop the update silently.

        # Mark user as "seen" for this window.
        self._cache[user_id] = True
        return await handler(event, data)
