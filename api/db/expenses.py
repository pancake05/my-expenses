from sqlmodel import select, func, SQLModel
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, date, timedelta, timezone, time as dt_time
from decimal import Decimal
from typing import Optional

from api.models.expense import Expense, ExpenseCreate, ExpenseResponse

# Moscow timezone (UTC+3)
MOSCOW_TZ = timezone(timedelta(hours=3))


def _get_moscow_today() -> date:
    """Get current date in Moscow timezone (UTC+3)."""
    return datetime.now(MOSCOW_TZ).date()


def _moscow_day_range(target_date: date):
    """Get start and end of a day in Moscow timezone as UTC datetimes."""
    moscow_midnight = datetime.combine(target_date, dt_time.min)
    moscow_midnight = moscow_midnight.replace(tzinfo=MOSCOW_TZ)
    utc_start = moscow_midnight.astimezone(timezone.utc).replace(tzinfo=None)
    # End of Moscow day = start of next Moscow day
    next_moscow = target_date + timedelta(days=1)
    utc_end = datetime.combine(next_moscow, dt_time.min).replace(tzinfo=MOSCOW_TZ)
    utc_end = utc_end.astimezone(timezone.utc).replace(tzinfo=None)
    return utc_start, utc_end


async def create_expense(session: AsyncSession, expense_data: ExpenseCreate) -> ExpenseResponse:
    expense = Expense(**expense_data.model_dump())
    session.add(expense)
    await session.commit()
    await session.refresh(expense)
    return ExpenseResponse.model_validate(expense)


async def get_last_expense(session: AsyncSession, telegram_user_id: int) -> Optional[ExpenseResponse]:
    statement = (
        select(Expense)
        .where(Expense.telegram_user_id == telegram_user_id)
        .order_by(Expense.created_at.desc())
        .limit(1)
    )
    result = await session.execute(statement)
    expense = result.scalars().first()
    if expense:
        return ExpenseResponse.model_validate(expense)
    return None


async def delete_last_expense(session: AsyncSession, telegram_user_id: int) -> Optional[ExpenseResponse]:
    last_expense = await get_last_expense(session, telegram_user_id)
    if last_expense is None:
        return None
    statement = (
        select(Expense)
        .where(Expense.id == last_expense.id)
    )
    result = await session.execute(statement)
    expense = result.scalars().first()
    if expense:
        await session.delete(expense)
        await session.commit()
    return last_expense


async def get_today_expenses(session: AsyncSession, telegram_user_id: int) -> list[ExpenseResponse]:
    today = _get_moscow_today()
    today_start, today_end = _moscow_day_range(today)
    statement = (
        select(Expense)
        .where(Expense.telegram_user_id == telegram_user_id)
        .where(Expense.created_at >= today_start)
        .where(Expense.created_at <= today_end)
        .order_by(Expense.created_at.desc())
    )
    result = await session.execute(statement)
    expenses = result.scalars().all()
    return [ExpenseResponse.model_validate(e) for e in expenses]


async def get_expenses_by_date(session: AsyncSession, telegram_user_id: int, target_date: date) -> list[ExpenseResponse]:
    day_start = datetime.combine(target_date, datetime.min.time())
    day_end = datetime.combine(target_date, datetime.max.time())
    statement = (
        select(Expense)
        .where(Expense.telegram_user_id == telegram_user_id)
        .where(Expense.created_at >= day_start)
        .where(Expense.created_at <= day_end)
        .order_by(Expense.created_at.desc())
    )
    result = await session.execute(statement)
    expenses = result.scalars().all()
    return [ExpenseResponse.model_validate(e) for e in expenses]


async def get_total_spent_today(session: AsyncSession, telegram_user_id: int) -> Decimal:
    today = _get_moscow_today()
    today_start, today_end = _moscow_day_range(today)
    statement = (
        select(func.sum(Expense.amount))
        .where(Expense.telegram_user_id == telegram_user_id)
        .where(Expense.created_at >= today_start)
        .where(Expense.created_at <= today_end)
    )
    result = await session.execute(statement)
    total = result.scalar()
    return total or Decimal("0")


async def get_expense_dates(session: AsyncSession, telegram_user_id: int) -> list[str]:
    from sqlalchemy import func as sa_func, Date, text
    date_col = Expense.created_at.cast(Date).label("expense_date")
    statement = (
        select(date_col)
        .where(Expense.telegram_user_id == telegram_user_id)
        .group_by(text("expense_date"))
        .order_by(text("expense_date DESC"))
    )
    result = await session.execute(statement)
    dates = result.scalars().all()
    return [d.isoformat() for d in dates]


async def get_prev_expense_date(session: AsyncSession, telegram_user_id: int, current_date: date) -> Optional[str]:
    from sqlalchemy import Date
    statement = (
        select(Expense.created_at.cast(Date))
        .where(Expense.telegram_user_id == telegram_user_id)
        .where(Expense.created_at.cast(Date) < current_date)
        .order_by(Expense.created_at.desc())
        .limit(1)
    )
    result = await session.execute(statement)
    d = result.scalars().first()
    return d.isoformat() if d else None


async def get_next_expense_date(session: AsyncSession, telegram_user_id: int, current_date: date) -> Optional[str]:
    from sqlalchemy import Date
    statement = (
        select(Expense.created_at.cast(Date))
        .where(Expense.telegram_user_id == telegram_user_id)
        .where(Expense.created_at.cast(Date) > current_date)
        .order_by(Expense.created_at.asc())
        .limit(1)
    )
    result = await session.execute(statement)
    d = result.scalars().first()
    return d.isoformat() if d else None
