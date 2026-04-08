"""
Inline Calendar Keyboard
========================
Renders a Telegram InlineKeyboardMarkup that looks like a month calendar.
Users tap a day button to select a date; ◀ / ▶ navigate between months.

Usage
-----
    from keyboards.calendar_kb import build_calendar, CalendarCallback

    # Show calendar for the current month
    await message.answer("📅 اختر التاريخ:", reply_markup=build_calendar())

    # Handle a callback
    @router.callback_query(CalendarCallback.filter())
    async def on_calendar(callback: types.CallbackQuery,
                          callback_data: CalendarCallback):
        action, year, month, day = (
            callback_data.action,
            callback_data.year,
            callback_data.month,
            callback_data.day,
        )
        if action == "day":
            date_str = f"{year:04d}-{month:02d}-{day:02d}"
            ...
        elif action == "nav":
            await callback.message.edit_reply_markup(
                reply_markup=build_calendar(year, month)
            )
"""

import calendar
from datetime import date, datetime, timezone

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ── Callback factory ──────────────────────────────────────────────────────────

class CalendarCallback(CallbackData, prefix="cal"):
    """Encodes every tap on the calendar keyboard.

    Actions
    -------
    day   : user tapped a day  → ``day`` holds the day number
    nav   : user tapped ◀/▶   → ``day`` is 0 (unused)
    ignore: cosmetic cells (header, padding) → do nothing
    """
    action: str   # "day" | "nav" | "ignore"
    year:   int
    month:  int
    day:    int   # 0 for nav / ignore


# ── Arabic month names ─────────────────────────────────────────────────────────

_MONTH_AR = [
    "", "يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
    "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر",
]

_WEEKDAYS_AR = ["الإث", "الثل", "الأر", "الخم", "الجم", "السب", "الأح"]


# ── Builder ───────────────────────────────────────────────────────────────────

def build_calendar(year: int = 0, month: int = 0) -> InlineKeyboardMarkup:
    """Return an inline keyboard for *month* of *year*.

    Defaults to the current UTC month when year/month are not provided.
    """
    today = date.today()
    if year == 0 or month == 0:
        year, month = today.year, today.month

    builder = InlineKeyboardBuilder()

    # ── Row 1: month / year header ─────────────────────────────────────────
    header_text = f"📅 {_MONTH_AR[month]} {year}"
    builder.button(
        text=header_text,
        callback_data=CalendarCallback(
            action="ignore", year=year, month=month, day=0
        ),
    )
    builder.adjust(1)

    # ── Row 2: ◀ prev | ▶ next navigation ─────────────────────────────────
    prev_year, prev_month = (year, month - 1) if month > 1 else (year - 1, 12)
    next_year, next_month = (year, month + 1) if month < 12 else (year + 1, 1)

    builder.row(
        _btn("◀️", "nav", prev_year, prev_month, 0),
        _btn("▶️", "nav", next_year, next_month, 0),
    )

    # ── Row 3: weekday labels ──────────────────────────────────────────────
    builder.row(*[
        _btn(wd, "ignore", year, month, 0)
        for wd in _WEEKDAYS_AR
    ])

    # ── Rows 4+: day grid ─────────────────────────────────────────────────
    # calendar.monthcalendar returns weeks as lists of 7 ints (0 = padding)
    for week in calendar.monthcalendar(year, month):
        row_buttons = []
        for day_num in week:
            if day_num == 0:
                # Padding cell
                row_buttons.append(
                    _btn(" ", "ignore", year, month, 0)
                )
            else:
                label = str(day_num)
                # Highlight today
                if day_num == today.day and month == today.month and year == today.year:
                    label = f"[{day_num}]"
                row_buttons.append(
                    _btn(label, "day", year, month, day_num)
                )
        builder.row(*row_buttons)

    return builder.as_markup()


# ── Private helpers ───────────────────────────────────────────────────────────

def _btn(text: str, action: str, year: int, month: int, day: int):
    """Shorthand for building a single InlineKeyboardButton."""
    from aiogram.types import InlineKeyboardButton
    return InlineKeyboardButton(
        text=text,
        callback_data=CalendarCallback(
            action=action, year=year, month=month, day=day
        ).pack(),
    )
