from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.accounts.models import AccountType, YieldType

HEX_COLOR = r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$"


class AccountBase(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    bank: str | None = Field(default=None, max_length=80)
    type: AccountType = AccountType.checking
    color: str = Field(default="#5E7CE2", pattern=HEX_COLOR)
    icon: str = Field(default="bank", max_length=40)

    # -- Rendimento ---------------------------------------------------------
    yield_type: YieldType = YieldType.none
    yield_rate: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        le=1000,
        description="Percentual do indice. 100 = 100% do CDI.",
    )
    yield_started_on: date | None = Field(
        default=None, description="A partir de quando o saldo rende."
    )


class AccountCreate(AccountBase):
    initial_balance: Decimal = Field(default=Decimal("0"), decimal_places=2)


class AccountUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    bank: str | None = Field(default=None, max_length=80)
    type: AccountType | None = None
    initial_balance: Decimal | None = Field(default=None, decimal_places=2)
    color: str | None = Field(default=None, pattern=HEX_COLOR)
    icon: str | None = Field(default=None, max_length=40)
    is_archived: bool | None = None
    yield_type: YieldType | None = None
    yield_rate: Decimal | None = Field(default=None, ge=0, le=1000)
    yield_started_on: date | None = None


class YieldInfo(BaseModel):
    """Situacao do rendimento da conta, para a interface ser honesta sobre ele."""

    # Rendimento ja acumulado no mes corrente, ainda nao creditado.
    projected_amount: Decimal
    projected_month: date
    business_days: int
    # Ultimo mes creditado como transacao.
    last_credited_month: date | None
    # None quando a fonte da taxa esta fora do ar.
    annual_rate: Decimal | None


class AccountRead(AccountBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    initial_balance: Decimal
    # Derivado das transacoes, nunca armazenado.
    current_balance: Decimal
    is_archived: bool
    created_at: datetime
    last_yield_month: date | None = None
    yield_info: YieldInfo | None = None


class AccountsSummary(BaseModel):
    total_balance: Decimal
    accounts: list[AccountRead]
    # Taxa vigente, exibida uma vez no topo em vez de repetida por conta.
    cdi_annual_rate: Decimal | None = None
