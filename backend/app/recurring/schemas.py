from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.recurring.models import Frequency
from app.transactions.models import TransactionType


class RecurringBase(BaseModel):
    description: str = Field(min_length=1, max_length=160)
    amount: Decimal = Field(gt=0, decimal_places=2)
    type: TransactionType
    frequency: Frequency = Frequency.monthly
    day_of_month: int | None = Field(default=None, ge=1, le=31)
    weekday: int | None = Field(default=None, ge=0, le=6, description="0 = segunda")
    month_of_year: int | None = Field(default=None, ge=1, le=12)
    start_date: date
    end_date: date | None = None
    is_active: bool = True
    category_id: uuid.UUID | None = None
    account_id: uuid.UUID | None = None
    card_id: uuid.UUID | None = None
    notes: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def _check_schedule(self) -> "RecurringBase":
        if self.type is TransactionType.transfer:
            raise ValueError("Transferencias nao podem ser recorrentes nesta versao.")
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("A data final deve ser posterior a inicial.")
        if self.frequency is Frequency.weekly and self.weekday is None:
            self.weekday = self.start_date.weekday()
        if self.frequency in (Frequency.monthly, Frequency.yearly) and self.day_of_month is None:
            self.day_of_month = self.start_date.day
        if self.frequency is Frequency.yearly and self.month_of_year is None:
            self.month_of_year = self.start_date.month
        return self


class RecurringCreate(RecurringBase):
    pass


class RecurringUpdate(BaseModel):
    description: str | None = Field(default=None, min_length=1, max_length=160)
    amount: Decimal | None = Field(default=None, gt=0, decimal_places=2)
    type: TransactionType | None = None
    frequency: Frequency | None = None
    day_of_month: int | None = Field(default=None, ge=1, le=31)
    weekday: int | None = Field(default=None, ge=0, le=6)
    month_of_year: int | None = Field(default=None, ge=1, le=12)
    start_date: date | None = None
    end_date: date | None = None
    is_active: bool | None = None
    category_id: uuid.UUID | None = None
    account_id: uuid.UUID | None = None
    card_id: uuid.UUID | None = None
    notes: str | None = Field(default=None, max_length=500)


class RecurringRead(RecurringBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime


class OccurrenceRead(BaseModel):
    rule_id: uuid.UUID
    description: str
    amount: Decimal
    type: TransactionType
    due_date: date
    category_id: uuid.UUID | None
    account_id: uuid.UUID | None
    card_id: uuid.UUID | None
    is_settled: bool


class ConfirmOccurrence(BaseModel):
    due_date: date
