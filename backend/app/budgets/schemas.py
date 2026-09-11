from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class BudgetWrite(BaseModel):
    month: date = Field(description="Qualquer dia do mes de referencia")
    category_id: uuid.UUID
    amount: Decimal = Field(ge=0, decimal_places=2)


class BudgetAmountUpdate(BaseModel):
    amount: Decimal = Field(ge=0, decimal_places=2)


class BudgetItem(BaseModel):
    id: uuid.UUID
    month: date
    category_id: uuid.UUID
    category_name: str
    category_color: str
    category_icon: str
    amount: Decimal
    spent: Decimal
    remaining: Decimal
    used_percentage: Decimal
    is_exceeded: bool


class BudgetSummary(BaseModel):
    month: date
    total_planned: Decimal
    total_spent: Decimal
    total_remaining: Decimal
    used_percentage: Decimal
    items: list[BudgetItem]
