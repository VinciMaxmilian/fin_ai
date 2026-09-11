from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

HEX_COLOR = r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$"


class GoalBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    target_amount: Decimal = Field(gt=0, decimal_places=2)
    target_date: date | None = None
    color: str = Field(default="#34C759", pattern=HEX_COLOR)
    icon: str = Field(default="target", max_length=40)
    notes: str | None = Field(default=None, max_length=500)


class GoalCreate(GoalBase):
    current_amount: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=2)


class GoalUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    target_amount: Decimal | None = Field(default=None, gt=0, decimal_places=2)
    current_amount: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    target_date: date | None = None
    color: str | None = Field(default=None, pattern=HEX_COLOR)
    icon: str | None = Field(default=None, max_length=40)
    notes: str | None = Field(default=None, max_length=500)
    is_archived: bool | None = None


class GoalContribution(BaseModel):
    amount: Decimal = Field(description="Positivo para aportar, negativo para resgatar")


class GoalRead(GoalBase):
    id: uuid.UUID
    current_amount: Decimal
    progress: Decimal
    remaining: Decimal
    is_completed: bool
    is_archived: bool
    created_at: datetime
