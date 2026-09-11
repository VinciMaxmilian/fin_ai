from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class InstallmentPlanUpdate(BaseModel):
    description: str | None = Field(default=None, min_length=1, max_length=160)
    category_id: uuid.UUID | None = None
    notes: str | None = Field(default=None, max_length=500)


class InstallmentPlanRead(BaseModel):
    id: uuid.UUID
    description: str
    total_amount: Decimal
    installments_count: int
    installment_amount: Decimal
    first_due_date: date
    card_id: uuid.UUID | None
    account_id: uuid.UUID | None
    category_id: uuid.UUID | None
    notes: str | None
    paid_installments: int
    remaining_installments: int
    paid_amount: Decimal
    remaining_amount: Decimal
    next_due_date: date | None
    is_completed: bool
    created_at: datetime
