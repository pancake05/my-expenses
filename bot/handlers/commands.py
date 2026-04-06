from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from bot.handlers.keyboards import get_start_keyboard, get_main_menu_keyboard
from bot.handlers.expense import ExpenseStates
from bot.handlers.keyboards import format_moscow_time_short

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    keyboard = get_start_keyboard()
    await message.answer(
        "💰 *Welcome to My Expenses!*\n\n"
        "Record your expenses quickly and see the latest spending.\n\n"
        "Use the buttons below to get started:",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📖 *Available Commands:*\n\n"
        "/start - Start the bot and see main menu\n"
        "/help - Show this help message\n"
        "/record - Record a new expense\n"
        "/today - View today's expenses\n"
        "/deletelast - Delete the last expense\n\n"
        "💡 *Quick Tip:* Just type an amount and I'll ask you for the category!",
        parse_mode="Markdown",
    )


@router.message(Command("record"))
async def cmd_record(message: Message, state: FSMContext):
    await state.set_state(ExpenseStates.waiting_for_amount)
    await message.answer(
        "💵 Enter what you spent on and the amount:",
    )


@router.message(Command("today"))
async def cmd_today(message: Message):
    from bot.services.expenses_api import api_client

    expenses = await api_client.get_today_expenses(message.from_user.id)
    if not expenses:
        await message.answer("📋 No expenses recorded today.")
        await message.answer(
            "💰 What would you like to do?",
            reply_markup=get_main_menu_keyboard(),
        )
        return

    total = await api_client.get_total_today(message.from_user.id)
    text = f"📋 *Today's Expenses*\n\n"
    for i, exp in enumerate(expenses, 1):
        time_str = format_moscow_time_short(exp["created_at"])
        category_emoji = {"Food": "🍔", "Transport": "🚗"}.get(exp["category"], "📦")
        text += f"{i}. 💰 {exp['amount']} — {category_emoji} {exp['category']}\n"
        text += f"   🕐 {time_str}\n\n"
    text += f"💰 *Total: {total}*"

    await message.answer(text, parse_mode="Markdown")
    await message.answer(
        "💰 What would you like to do?",
        reply_markup=get_main_menu_keyboard(),
    )


@router.message(Command("deletelast"))
async def cmd_delete_last(message: Message):
    from bot.services.expenses_api import api_client

    deleted = await api_client.delete_last_expense(message.from_user.id)
    if deleted:
        await message.answer(
            f"🗑 Last expense deleted: *{deleted['amount']} - {deleted['category']}*",
            parse_mode="Markdown",
        )
    else:
        await message.answer("❌ No expenses to delete.")
    await message.answer(
        "💰 What would you like to do?",
        reply_markup=get_main_menu_keyboard(),
    )
