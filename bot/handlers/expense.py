from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import date

from bot.handlers.keyboards import (
    get_category_keyboard,
    get_main_menu_keyboard,
    get_date_selection_keyboard,
    get_date_navigation_keyboard,
    get_confirm_keyboard,
    format_moscow_time_short,
)
from bot.services.expenses_api import api_client
from bot.services.local_expense_parser import parse_expense

router = Router()


class ExpenseStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_category = State()
    llm_confirm = State()


@router.message(ExpenseStates.waiting_for_amount)
async def process_amount(message: Message, state: FSMContext):
    text = message.text.strip().replace(",", ".")

    # Try parsing as a plain number first
    try:
        amount = float(text)
        if amount <= 0:
            await message.answer("❌ Please enter a positive number.")
            return
        await state.update_data(amount=amount)
        await state.set_state(ExpenseStates.waiting_for_category)
        await message.answer(
            "📂 Select a category:",
            reply_markup=get_category_keyboard(),
        )
        return
    except ValueError:
        pass  # Not a plain number, try local parser

    # Fall back to local expense parsing
    parsed = parse_expense(text)

    if parsed and not parsed.error and parsed.amount > 0:
        await state.update_data(
            amount=parsed.amount,
            category=parsed.category,
            description=parsed.description,
        )
        await state.set_state(ExpenseStates.llm_confirm)

        category_emoji = {"Food": "🍔", "Transport": "🚗"}.get(parsed.category, "📦")
        desc_text = f"\n📝 {parsed.description}" if parsed.description else ""
        await message.answer(
            f"📋 *Record expense?*\n\n"
            f"💵 Amount: *{parsed.amount}*\n"
            f"📂 Category: {category_emoji} *{parsed.category}*{desc_text}",
            parse_mode="Markdown",
            reply_markup=get_confirm_keyboard(),
        )
        return

    await message.answer("❌ Invalid amount. Please enter a number (e.g., 150.50):")


# ---------- LLM-powered expense parsing ----------

@router.message(F.text, ~F.from_user.state)
async def llm_parse_expense_fallback(message: Message, state: FSMContext):
    """Handle free-text expense descriptions using local parser."""
    current_state = await state.get_state()
    if current_state is not None:
        return  # Some other handler is active

    text = message.text.strip()
    if len(text) < 3:
        return  # Too short, ignore

    parsed = parse_expense(text)

    if parsed is None or parsed.error:
        await message.answer(
            "🤔 I couldn't understand the expense. Please try again or use the buttons below.",
            reply_markup=get_main_menu_keyboard(),
        )
        return

    category_emoji = {"Food": "🍔", "Transport": "🚗"}.get(parsed.category, "📦")

    await state.update_data(
        amount=parsed.amount,
        category=parsed.category,
        description=parsed.description,
    )
    await state.set_state(ExpenseStates.llm_confirm)

    desc_text = f"\n📝 {parsed.description}" if parsed.description else ""
    await message.answer(
        f"📋 *Record expense?*\n\n"
        f"💵 Amount: *{parsed.amount}*\n"
        f"📂 Category: {category_emoji} *{parsed.category}*{desc_text}",
        parse_mode="Markdown",
        reply_markup=get_confirm_keyboard(),
    )


@router.callback_query(lambda c: c.data.startswith("llm_confirm:"))
async def llm_confirm_callback(callback: CallbackQuery, state: FSMContext):
    """Confirm or cancel LLM-parsed expense via buttons."""
    action = callback.data.split(":")[1]

    if action == "yes":
        data = await state.get_data()
        amount = data.get("amount")
        category = data.get("category")
        description = data.get("description")

        expense = await api_client.create_expense(
            telegram_user_id=callback.from_user.id,
            amount=amount,
            category=category,
            description=description,
        )

        if expense:
            await state.clear()
            time_str = format_moscow_time_short(expense["created_at"])
            category_emoji = {"Food": "🍔", "Transport": "🚗"}.get(expense["category"], "📦")
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
            await state.clear()
            await callback.message.edit_text("❌ Failed to record expense. Please try again.")
            await callback.message.answer(
                "💰 What would you like to do?",
                reply_markup=get_main_menu_keyboard(),
            )
    elif action == "other":
        # Save as "Other" category regardless of what LLM detected
        data = await state.get_data()
        amount = data.get("amount")
        description = data.get("description")

        expense = await api_client.create_expense(
            telegram_user_id=callback.from_user.id,
            amount=amount,
            category="Other",
            description=description,
        )

        if expense:
            await state.clear()
            time_str = format_moscow_time_short(expense["created_at"])
            await callback.message.edit_text(
                f"✅ *Expense Recorded!*\n\n"
                f"💵 Amount: {expense['amount']}\n"
                f"📂 Category: 📦 {expense['category']}\n"
                f"🕐 Time: {time_str}",
                parse_mode="Markdown",
            )
            await callback.message.answer(
                "💰 What would you like to do next?",
                reply_markup=get_main_menu_keyboard(),
            )
        else:
            await state.clear()
            await callback.message.edit_text("❌ Failed to record expense. Please try again.")
            await callback.message.answer(
                "💰 What would you like to do?",
                reply_markup=get_main_menu_keyboard(),
            )
    else:
        await state.clear()
        await callback.message.edit_text("❌ Expense recording cancelled.")
        await callback.message.answer(
            "💰 What would you like to do?",
            reply_markup=get_main_menu_keyboard(),
        )

    await callback.answer()


@router.callback_query(ExpenseStates.waiting_for_category)
async def process_category(callback: CallbackQuery, state: FSMContext):
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
    text = f"📋 *Today's Expenses*\n\n"
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

    expenses = await api_client.get_expenses_by_date(telegram_user_id, target_date)

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
