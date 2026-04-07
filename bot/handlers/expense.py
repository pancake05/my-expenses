import re
from datetime import date

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot.handlers.keyboards import (
    format_moscow_time_short,
    get_category_keyboard,
    get_date_navigation_keyboard,
    get_date_selection_keyboard,
    get_llm_confirm_keyboard,
    get_main_menu_keyboard,
)
from bot.services.expenses_api import api_client
from bot.services.llm_parser import llm_parser

router = Router()


class ExpenseStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_llm_confirm = State()


def _is_llm_trigger(text: str) -> bool:
    """
    Detect if input looks like a natural-language expense description.
    Examples: 'bus 300', 'lunch 500', 'taxi 1200', 'coffee 150'.

    Heuristic: text contains at least one alphabetic word AND a number.
    Pure numeric inputs (like '300' or '300.50') are NOT LLM triggers.
    """
    text = text.strip()
    has_alpha = bool(re.search(r"[a-zA-Zа-яА-ЯёЁ]", text))
    has_number = bool(re.search(r"\d", text))
    return has_alpha and has_number


@router.message(ExpenseStates.waiting_for_amount)
async def process_amount(message: Message, state: FSMContext):
    """Extract amount — either pure number (classic flow) or natural text (LLM flow)."""
    text = message.text.strip()

    if _is_llm_trigger(text):
        await _handle_llm_flow(message, state, text)
        return

    # Classic flow: pure numeric amount
    cleaned = text.replace(",", ".")
    try:
        amount = float(cleaned)
        if amount <= 0:
            await message.answer("❌ Please enter a positive number.")
            return
    except ValueError:
        await message.answer("❌ Invalid amount. Please enter a number (e.g., 150.50):")
        return

    await state.update_data(amount=amount)
    await message.answer(
        "📂 Select a category:",
        reply_markup=get_category_keyboard(),
    )


async def _handle_llm_flow(message: Message, state: FSMContext, text: str):
    """Send text to LLM, then show confirmation dialog. Falls back to manual parsing."""
    await message.answer("🤖 Analyzing your expense...")

    result = await llm_parser.parse_expense(text)

    if result is None:
        # Fallback: try to extract amount from text manually
        cleaned = text.replace(",", ".")
        numbers = re.findall(r"[\d]+\.?[\d]*", cleaned)
        if numbers:
            amount = float(numbers[-1])  # Take the last number found
            if amount > 0:
                await state.update_data(
                    amount=amount,
                    llm_category="Other",
                    llm_description=text,
                )
                await state.set_state(ExpenseStates.waiting_for_llm_confirm)
                await message.answer(
                    f"🤖 I couldn't auto-detect the category, but I found the amount:\n\n"
                    f"💵 Amount: *{amount}*\n"
                    f"📂 Category: 📦 *Other*\n"
                    f"📝 Description: {text}\n\n"
                    f"Confirm or adjust:",
                    reply_markup=get_llm_confirm_keyboard(),
                    parse_mode="Markdown",
                )
                return

        await message.answer(
            "❌ Couldn't parse the expense. Please try again with a clear format, e.g. 'bus 300'."
        )
        await message.answer(
            "💰 What would you like to do?",
            reply_markup=get_main_menu_keyboard(),
        )
        return

    await state.update_data(
        amount=result["amount"],
        llm_category=result["category"],
        llm_description=result["description"],
    )
    await state.set_state(ExpenseStates.waiting_for_llm_confirm)

    category_emoji = {"Food": "🍔", "Transport": "🚗"}.get(result["category"], "📦")

    await message.answer(
        f"🤖 I understood:\n\n"
        f"💵 Amount: *{result['amount']}*\n"
        f"📂 Category: {category_emoji} *{result['category']}*\n"
        f"📝 Description: {result['description']}\n\n"
        f"Confirm or adjust:",
        reply_markup=get_llm_confirm_keyboard(),
        parse_mode="Markdown",
    )


@router.callback_query(ExpenseStates.waiting_for_llm_confirm)
async def process_llm_confirm(callback: CallbackQuery, state: FSMContext):
    """Handle Yes / No / Save as Other for LLM-parsed expense."""
    data = await state.get_data()
    amount = data.get("amount")
    llm_category = data.get("llm_category")
    llm_description = data.get("llm_description", "")

    if callback.data == "llm_confirm:no":
        # Cancel entirely
        await state.clear()
        await callback.message.edit_text("❌ Expense recording cancelled.")
        await callback.message.answer(
            "💰 What would you like to do?",
            reply_markup=get_main_menu_keyboard(),
        )
        await callback.answer()
        return

    # Determine final category
    if callback.data == "llm_confirm:other":
        category = "Other"
        category_emoji = "📦"
    else:
        category = llm_category
        category_emoji = {"Food": "🍔", "Transport": "🚗"}.get(category, "📦")

    expense = await api_client.create_expense(
        telegram_user_id=callback.from_user.id,
        amount=amount,
        category=category,
        description=llm_description,
    )

    if expense:
        await state.clear()
        time_str = format_moscow_time_short(expense["created_at"])
        await callback.message.edit_text(
            f"✅ *Expense Recorded!*\n\n"
            f"💵 Amount: {expense['amount']}\n"
            f"📂 Category: {category_emoji} {expense['category']}\n"
            f"📝 {llm_description}\n"
            f"🕐 Time: {time_str}",
            parse_mode="Markdown",
        )
        await callback.message.answer(
            "💰 What would you like to do next?",
            reply_markup=get_main_menu_keyboard(),
        )
    else:
        await callback.message.edit_text("❌ Failed to record expense. Please try again.")

    await callback.answer()


@router.callback_query(ExpenseStates.waiting_for_amount)
async def process_category(callback: CallbackQuery, state: FSMContext):
    """User selected a category — create the expense."""
    data = await state.get_data()
    amount = data.get("amount")

    if callback.data == "cancel":
        await state.clear()
        await callback.message.edit_text("❌ Expense recording cancelled.")
        await callback.message.answer(
            "💰 What would you like to do?",
            reply_markup=get_main_menu_keyboard(),
        )
        await callback.answer()
        return

    if callback.data.startswith("cat:"):
        category = callback.data.split(":")[1].capitalize()
        if category == "Food":
            category_emoji = "🍔"
        elif category == "Transport":
            category_emoji = "🚗"
        else:
            category_emoji = "📦"

        expense = await api_client.create_expense(
            telegram_user_id=callback.from_user.id,
            amount=amount,
            category=category,
        )

        if expense:
            await state.clear()
            time_str = format_moscow_time_short(expense["created_at"])
            await callback.message.edit_text(
                f"✅ *Expense Recorded!*\n\n"
                f"💵 Amount: {expense['amount']}\n"
                f"📂 Category: {category_emoji} {expense['category']}\n"
                f"🕐 Time: {time_str}",
                parse_mode="Markdown",
            )
            await callback.message.answer(
                "💰 What would you like to do next?",
                reply_markup=get_main_menu_keyboard(),
            )
        else:
            await callback.message.edit_text("❌ Failed to record expense. Please try again.")

    await callback.answer()


@router.callback_query(lambda c: c.data == "record")
async def callback_record(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ExpenseStates.waiting_for_amount)
    await callback.message.edit_text("💵 Enter what you spent on and the amount:")
    await callback.answer()


@router.callback_query(lambda c: c.data == "today")
async def callback_today(callback: CallbackQuery):
    expenses = await api_client.get_today_expenses(callback.from_user.id)
    if not expenses:
        await callback.message.edit_text("📋 No expenses recorded today.")
        await callback.message.answer(
            "💰 What would you like to do?",
            reply_markup=get_main_menu_keyboard(),
        )
        await callback.answer()
        return

    total = await api_client.get_total_today(callback.from_user.id)
    text = "📋 *Today's Expenses*\n\n"
    for i, exp in enumerate(expenses, 1):
        time_str = format_moscow_time_short(exp["created_at"])
        category_emoji = {"Food": "🍔", "Transport": "🚗"}.get(exp["category"], "📦")
        text += f"{i}. 💰 {exp['amount']} — {category_emoji} {exp['category']}\n"
        text += f"   🕐 {time_str}\n\n"
    text += f"💰 *Total: {total}*"

    await callback.message.edit_text(text, parse_mode="Markdown")
    await callback.message.answer(
        "💰 What would you like to do?",
        reply_markup=get_main_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "delete_last")
async def callback_delete_last(callback: CallbackQuery):
    deleted = await api_client.delete_last_expense(callback.from_user.id)
    if deleted:
        await callback.message.edit_text(
            f"🗑 Last expense deleted: *{deleted['amount']} - {deleted['category']}*",
            parse_mode="Markdown",
        )
    else:
        await callback.message.edit_text("❌ No expenses to delete.")
    await callback.message.answer(
        "💰 What would you like to do?",
        reply_markup=get_main_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "noop_prev")
async def callback_noop_prev(callback: CallbackQuery):
    await callback.answer("⛔ No expenses before this date.", show_alert=True)


@router.callback_query(lambda c: c.data == "noop_next")
async def callback_noop_next(callback: CallbackQuery):
    await callback.answer("⛔ No expenses after this date.", show_alert=True)


@router.callback_query(lambda c: c.data == "by_date")
async def callback_by_date(callback: CallbackQuery):
    dates = await api_client.get_expense_dates(callback.from_user.id)
    if not dates:
        await callback.message.edit_text("📅 No expenses recorded yet.")
        await callback.message.answer(
            "💰 What would you like to do?",
            reply_markup=get_main_menu_keyboard(),
        )
        await callback.answer()
        return

    await callback.message.edit_text("📅 *Select a date:*\n\nChoose a date to view expenses:", parse_mode="Markdown")
    await callback.message.answer(
        "📅 *Your expense dates:*\n(Select to view details)",
        reply_markup=get_date_selection_keyboard(dates),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("pick_date:"))
async def callback_pick_date(callback: CallbackQuery):
    target_date_str = callback.data.split(":", 1)[1]
    try:
        target_date = date.fromisoformat(target_date_str)
    except ValueError:
        await callback.answer("❌ Invalid date.", show_alert=True)
        return

    await show_expenses_for_date(callback.message, callback.from_user.id, target_date)
    await callback.answer()


@router.callback_query(lambda c: c.data == "close_date_view")
async def callback_close_date_view(callback: CallbackQuery):
    await callback.message.edit_text("📅 Date view closed.")
    await callback.message.answer(
        "💰 What would you like to do?",
        reply_markup=get_main_menu_keyboard(),
    )
    await callback.answer()


async def show_expenses_for_date(message, telegram_user_id: int, target_date: date):
    from decimal import Decimal

    target_date_str = target_date.strftime("%d.%m.%Y")
    current_iso = target_date.isoformat()

    expenses = await api_client.get_expenses_by_date(telegram_user_id, current_iso)

    # Check prev/next dates
    prev_date = await api_client.get_prev_expense_date(telegram_user_id, current_iso)
    next_date = await api_client.get_next_expense_date(telegram_user_id, current_iso)

    if not expenses:
        text = f"📅 *{target_date_str}*\n\nNo expenses recorded on this date."
        await message.edit_text(text, parse_mode="Markdown")
        await message.answer(
            "💰 What would you like to do?",
            reply_markup=get_main_menu_keyboard(),
        )
        return

    # Calculate total
    total = sum(Decimal(exp["amount"]) for exp in expenses)

    text = f"📅 *Expenses for {target_date_str}*\n\n"
    for i, exp in enumerate(expenses, 1):
        time_str = format_moscow_time_short(exp["created_at"])
        category_emoji = {"Food": "🍔", "Transport": "🚗"}.get(exp["category"], "📦")
        text += f"{i}. 💰 {exp['amount']} — {category_emoji} {exp['category']}\n"
        text += f"   🕐 {time_str}\n\n"
    text += f"💰 *Total: {total}*"

    await message.edit_text(text, parse_mode="Markdown")
    await message.answer(
        "💰 Navigate dates or go back:",
        reply_markup=get_date_navigation_keyboard(target_date, prev_date, next_date),
    )
