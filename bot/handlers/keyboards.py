from typing import Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import date, timedelta, datetime, timezone, time as dt_time


def format_moscow_time(utc_iso: str) -> str:
    """Convert UTC ISO timestamp to Moscow time (UTC+3) formatted string."""
    utc_dt = datetime.fromisoformat(utc_iso.replace("Z", "+00:00"))
    moscow_tz = timezone(timedelta(hours=3))
    moscow_dt = utc_dt.astimezone(moscow_tz)
    return moscow_dt.strftime("%d.%m.%Y %H:%M")


def format_moscow_time_short(utc_iso: str) -> str:
    """Convert UTC ISO timestamp to short Moscow time (HH:MM)."""
    utc_dt = datetime.fromisoformat(utc_iso.replace("Z", "+00:00"))
    moscow_tz = timezone(timedelta(hours=3))
    moscow_dt = utc_dt.astimezone(moscow_tz)
    return moscow_dt.strftime("%H:%M")


def get_start_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📝 Record Expense", callback_data="record"),
            ],
            [
                InlineKeyboardButton(text="📋 Today's Expenses", callback_data="today"),
                InlineKeyboardButton(text="🗑 Delete Last", callback_data="delete_last"),
            ],
            [
                InlineKeyboardButton(text="📅 Expenses by Date", callback_data="by_date"),
            ],
        ]
    )
    return keyboard


def get_category_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🍔 Food", callback_data="cat:food"),
                InlineKeyboardButton(text="🚗 Transport", callback_data="cat:transport"),
                InlineKeyboardButton(text="📦 Other", callback_data="cat:other"),
            ],
            [
                InlineKeyboardButton(text="❌ Cancel", callback_data="cancel"),
            ],
        ]
    )
    return keyboard


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📝 Record Expense", callback_data="record"),
            ],
            [
                InlineKeyboardButton(text="📋 Today's Expenses", callback_data="today"),
                InlineKeyboardButton(text="🗑 Delete Last", callback_data="delete_last"),
            ],
            [
                InlineKeyboardButton(text="📅 Expenses by Date", callback_data="by_date"),
            ],
        ]
    )
    return keyboard


def get_date_selection_keyboard(dates: list[str]) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[]
    )

    for d in dates:
        date_obj = date.fromisoformat(d)
        display = date_obj.strftime("%d.%m.%Y")
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text=f"📅 {display}", callback_data=f"pick_date:{d}")
        ])

    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="❌ Close", callback_data="close_date_view"),
    ])

    return keyboard


def get_date_navigation_keyboard(selected_date: date, prev_date: Optional[str], next_date: Optional[str]) -> InlineKeyboardMarkup:
    date_str = selected_date.strftime("%d.%m.%Y")

    row = []
    if prev_date:
        row.append(InlineKeyboardButton(text="◀️", callback_data=f"pick_date:{prev_date}"))
    else:
        row.append(InlineKeyboardButton(text="⛔", callback_data="noop_prev"))

    row.append(InlineKeyboardButton(text=f"📅 {date_str}", callback_data="noop"))

    if next_date:
        row.append(InlineKeyboardButton(text="▶️", callback_data=f"pick_date:{next_date}"))
    else:
        row.append(InlineKeyboardButton(text="⛔", callback_data="noop_next"))

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            row,
            [
                InlineKeyboardButton(text="📋 Today", callback_data="today"),
                InlineKeyboardButton(text="🔙 All Dates", callback_data="by_date"),
            ],
        ]
    )
    return keyboard


def get_confirm_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Yes", callback_data="llm_confirm:yes"),
                InlineKeyboardButton(text="❌ No", callback_data="llm_confirm:no"),
            ],
            [
                InlineKeyboardButton(text="💾 Save as Other", callback_data="llm_confirm:other"),
            ],
        ]
    )
    return keyboard
