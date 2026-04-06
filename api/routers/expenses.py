from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_session
from api.models.expense import ExpenseCreate, ExpenseResponse
from api.db import expenses as expenses_db
from datetime import date
from decimal import Decimal

router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.post("/", response_model=ExpenseResponse)
async def create_new_expense(
    data: ExpenseCreate,
    session: AsyncSession = Depends(get_session),
):
    return await expenses_db.create_expense(session, data)


@router.get("/last/{telegram_user_id}", response_model=ExpenseResponse | None)
async def get_latest_expense(
    telegram_user_id: int,
    session: AsyncSession = Depends(get_session),
):
    return await expenses_db.get_last_expense(session, telegram_user_id)


@router.delete("/last/{telegram_user_id}", response_model=ExpenseResponse | None)
async def delete_latest_expense(
    telegram_user_id: int,
    session: AsyncSession = Depends(get_session),
):
    return await expenses_db.delete_last_expense(session, telegram_user_id)


@router.get("/today/{telegram_user_id}", response_model=list[ExpenseResponse])
async def get_today_expenses(
    telegram_user_id: int,
    session: AsyncSession = Depends(get_session),
):
    return await expenses_db.get_today_expenses(session, telegram_user_id)


@router.get("/date/{telegram_user_id}/{target_date}", response_model=list[ExpenseResponse])
async def get_expenses_by_date(
    telegram_user_id: int,
    target_date: date,
    session: AsyncSession = Depends(get_session),
):
    return await expenses_db.get_expenses_by_date(session, telegram_user_id, target_date)


@router.get("/total-today/{telegram_user_id}", response_model=dict)
async def get_total_today(
    telegram_user_id: int,
    session: AsyncSession = Depends(get_session),
):
    total = await expenses_db.get_total_spent_today(session, telegram_user_id)
    return {"total": str(total)}


@router.get("/dates/{telegram_user_id}", response_model=list[str])
async def get_expense_dates(
    telegram_user_id: int,
    session: AsyncSession = Depends(get_session),
):
    dates = await expenses_db.get_expense_dates(session, telegram_user_id)
    return dates


@router.get("/prev-date/{telegram_user_id}/{current_date}")
async def get_prev_date(
    telegram_user_id: int,
    current_date: date,
    session: AsyncSession = Depends(get_session),
):
    result = await expenses_db.get_prev_expense_date(session, telegram_user_id, current_date)
    return {"date": result}


@router.get("/next-date/{telegram_user_id}/{current_date}")
async def get_next_date(
    telegram_user_id: int,
    current_date: date,
    session: AsyncSession = Depends(get_session),
):
    result = await expenses_db.get_next_expense_date(session, telegram_user_id, current_date)
    return {"date": result}
