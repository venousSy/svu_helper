"""
Pagination helpers
==================
Generic utilities for slicing lists into fixed-size pages and building the
shared ⬅️ / 📄 X/N / ➡️ navigation keyboard used throughout the bot.
"""
from __future__ import annotations

from typing import Any

from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder

from keyboards.callbacks import MenuCallback, PageCallback, MenuAction, PageAction

PAGE_SIZE: int = 5


def paginate(
    items: list[Any],
    page: int,
    page_size: int = PAGE_SIZE,
) -> tuple[list[Any], int, int]:
    """
    Slice *items* for the requested *page*.

    Returns:
        (page_slice, total_pages, clamped_page)
    """
    total = len(items)
    total_pages = max(1, -(-total // page_size))   # ceiling division
    page = max(0, min(page, total_pages - 1))
    start = page * page_size
    return items[start : start + page_size], total_pages, page


def build_nav_keyboard(
    action: Any,
    page: int,
    total_pages: int,
    back_action: Any = MenuAction.back_to_admin,
    builder: InlineKeyboardBuilder | None = None,
) -> types.InlineKeyboardMarkup:
    """
    Build a standard navigation row + back button.
    If 'builder' is provided, append the rows to it.

    ⬅️ السابق  |  📄 X/N  |  التالي ➡️
              ⬅️ رجوع
    """
    if builder is None:
        builder = InlineKeyboardBuilder()

    nav: list[types.InlineKeyboardButton] = []

    if page > 0:
        nav.append(
            types.InlineKeyboardButton(
                text="⬅️ السابق",
                callback_data=PageCallback(action=action, page=page - 1).pack(),
            )
        )

    nav.append(
        types.InlineKeyboardButton(
            text=f"📄 {page + 1}/{total_pages}",
            callback_data="noop",
        )
    )

    if page < total_pages - 1:
        nav.append(
            types.InlineKeyboardButton(
                text="التالي ➡️",
                callback_data=PageCallback(action=action, page=page + 1).pack(),
            )
        )

    builder.row(*nav)
    builder.row(
        types.InlineKeyboardButton(
            text="⬅️ رجوع",
            callback_data=MenuCallback(action=back_action).pack(),
        )
    )
    return builder.as_markup()
