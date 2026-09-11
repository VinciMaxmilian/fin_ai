from __future__ import annotations

import uuid
import datetime as dt
from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from app.cards.schemas import CardRead
from app.transactions.models import TransactionType


class Overview(BaseModel):
    reference_month: date
    net_worth: Decimal
    available_balance: Decimal
    invested_amount: Decimal
    open_invoices: Decimal
    income: Decimal
    expenses: Decimal
    balance: Decimal


class CashFlowPoint(BaseModel):
    date: dt.date
    income: Decimal
    expenses: Decimal
    balance: Decimal


class CashFlow(BaseModel):
    period: str
    granularity: str
    start_date: date
    end_date: date
    total_income: Decimal
    total_expenses: Decimal
    total_balance: Decimal
    points: list[CashFlowPoint]


class CategorySlice(BaseModel):
    category_id: uuid.UUID | None
    name: str
    color: str
    icon: str
    amount: Decimal
    percentage: Decimal


class CategoryBreakdown(BaseModel):
    start_date: date
    end_date: date
    total: Decimal
    items: list[CategorySlice]


class UpcomingBill(BaseModel):
    kind: str
    reference_id: uuid.UUID
    description: str
    amount: Decimal
    due_date: date


class Dashboard(BaseModel):
    overview: Overview
    cash_flow: CashFlow
    expenses_by_category: CategoryBreakdown
    upcoming_bills: list[UpcomingBill]
    cards: list[CardRead]


class MonthlyPoint(BaseModel):
    month: date
    income: Decimal
    expenses: Decimal
    balance: Decimal
    cumulative_balance: Decimal


class MonthlySeries(BaseModel):
    start_date: date
    end_date: date
    points: list[MonthlyPoint]


class NetWorthPoint(BaseModel):
    month: date
    accounts_balance: Decimal
    invested_amount: Decimal
    net_worth: Decimal


class NetWorthEvolution(BaseModel):
    points: list[NetWorthPoint]


class CardSlice(BaseModel):
    card_id: uuid.UUID
    name: str
    color: str
    amount: Decimal
    percentage: Decimal


class CardSpending(BaseModel):
    start_date: date
    end_date: date
    total: Decimal
    items: list[CardSlice]


class RecurringItem(BaseModel):
    rule_id: uuid.UUID
    description: str
    amount: Decimal
    type: TransactionType
    due_date: date
    is_settled: bool


class RecurringSummary(BaseModel):
    month: date
    recurring_income: Decimal
    recurring_expenses: Decimal
    net: Decimal
    items: list[RecurringItem]
