from __future__ import annotations

import uuid
import datetime as dt
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.transactions.models import TransactionType


class TransactionBase(BaseModel):
    type: TransactionType
    amount: Decimal = Field(gt=0, decimal_places=2, description="Sempre positivo")
    description: str = Field(min_length=1, max_length=160)
    date: dt.date
    category_id: uuid.UUID | None = None
    account_id: uuid.UUID | None = None
    card_id: uuid.UUID | None = None
    transfer_account_id: uuid.UUID | None = None
    notes: str | None = Field(default=None, max_length=500)


class TransactionCreate(TransactionBase):
    # Quando maior que 1, o lancamento vira um parcelamento e o backend gera
    # uma transacao por parcela.
    installments: int = Field(default=1, ge=1, le=420)

    @model_validator(mode="after")
    def _check_consistency(self) -> "TransactionCreate":
        if self.type is TransactionType.transfer:
            if not self.account_id or not self.transfer_account_id:
                raise ValueError("Transferencia exige conta de origem e de destino.")
            if self.account_id == self.transfer_account_id:
                raise ValueError("A conta de origem e a de destino devem ser diferentes.")
            if self.card_id:
                raise ValueError("Transferencia nao pode ser lancada em cartao.")
            if self.installments > 1:
                raise ValueError("Transferencia nao pode ser parcelada.")
        else:
            if not self.account_id and not self.card_id:
                raise ValueError("Informe uma conta ou um cartao para o lancamento.")
            if self.transfer_account_id:
                raise ValueError("Conta de destino so se aplica a transferencias.")
            if self.card_id and self.type is TransactionType.income:
                raise ValueError("Receita nao pode ser lancada em cartao de credito.")
        return self


class TransactionUpdate(BaseModel):
    type: TransactionType | None = None
    amount: Decimal | None = Field(default=None, gt=0, decimal_places=2)
    description: str | None = Field(default=None, min_length=1, max_length=160)
    date: dt.date | None = None
    category_id: uuid.UUID | None = None
    account_id: uuid.UUID | None = None
    card_id: uuid.UUID | None = None
    transfer_account_id: uuid.UUID | None = None
    notes: str | None = Field(default=None, max_length=500)


class CategoryRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    color: str
    icon: str


class TransactionRead(TransactionBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    installment_plan_id: uuid.UUID | None
    installment_number: int | None
    recurring_rule_id: uuid.UUID | None
    created_at: dt.datetime
    updated_at: dt.datetime
    category: CategoryRef | None = None


SortField = Literal["date", "amount", "description", "created_at"]
SortOrder = Literal["asc", "desc"]


class TransactionFilters(BaseModel):
    """Filtros aceitos na listagem. Todos opcionais e combinaveis."""

    search: str | None = None
    type: TransactionType | None = None
    category_id: uuid.UUID | None = None
    account_id: uuid.UUID | None = None
    card_id: uuid.UUID | None = None
    date_from: dt.date | None = None
    date_to: dt.date | None = None
    amount_min: Decimal | None = None
    amount_max: Decimal | None = None
    sort_by: SortField = "date"
    sort_order: SortOrder = "desc"
