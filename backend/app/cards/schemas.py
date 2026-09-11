from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.cards.models import CardBrand

HEX_COLOR = r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$"


class CardBase(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    bank: str | None = Field(default=None, max_length=80)
    brand: CardBrand = CardBrand.other
    limit_amount: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=2)
    closing_day: int = Field(ge=1, le=31, description="Dia do fechamento da fatura")
    due_day: int = Field(ge=1, le=31, description="Dia do vencimento da fatura")
    account_id: uuid.UUID | None = Field(
        default=None, description="Conta de onde a fatura e debitada"
    )
    color: str = Field(default="#1C1C1E", pattern=HEX_COLOR)


class CardCreate(CardBase):
    pass


class CardUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    bank: str | None = Field(default=None, max_length=80)
    brand: CardBrand | None = None
    limit_amount: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    closing_day: int | None = Field(default=None, ge=1, le=31)
    due_day: int | None = Field(default=None, ge=1, le=31)
    account_id: uuid.UUID | None = None
    color: str | None = Field(default=None, pattern=HEX_COLOR)
    is_archived: bool | None = None


class InvoiceRead(BaseModel):
    """Uma fatura, identificada pela data de fechamento."""

    card_id: uuid.UUID
    period_start: date
    period_end: date
    closing_date: date
    due_date: date
    total: Decimal
    transactions_count: int
    # open   = ainda aceita compras
    # closed = fechada, aguardando vencimento
    # due    = venceu
    status: str


class CardRead(CardBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    is_archived: bool
    created_at: datetime
    # Total ja comprometido em faturas ainda nao pagas.
    used_limit: Decimal
    available_limit: Decimal
    current_invoice: InvoiceRead | None = None
