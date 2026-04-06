from sqlmodel import SQLModel, Field
from datetime import datetime
from decimal import Decimal
from typing import Optional


class Expense(SQLModel, table=True):
    __tablename__ = "expense"

    id: Optional[int] = Field(default=None, primary_key=True)
    telegram_user_id: int = Field(index=True)
    amount: Decimal = Field(max_digits=10, decimal_places=2)
    category: str = Field(max_length=50)
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ExpenseCreate(SQLModel):
    telegram_user_id: int
    amount: Decimal
    category: str
    description: Optional[str] = None


class ExpenseResponse(SQLModel):
    id: int
    telegram_user_id: int
    amount: Decimal
    category: str
    description: Optional[str]
    created_at: datetime


class DaySummary(SQLModel):
    date: str
    total_amount: Decimal
    count: int
    expenses: list[ExpenseResponse]
