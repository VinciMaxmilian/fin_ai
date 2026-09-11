from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.investments.models import InvestmentType

# De onde veio o preco usado no calculo. A interface usa isso para ser honesta
# sobre o numero que esta mostrando.
PriceSource = Literal["quote", "stale_quote", "manual", "average_price"]


class InvestmentBase(BaseModel):
    asset: str = Field(min_length=1, max_length=80, description="Nome do ativo")
    ticker: str | None = Field(
        default=None,
        max_length=16,
        description="Codigo de negociacao. Preenchido, o preco atual e buscado automaticamente.",
    )
    type: InvestmentType = InvestmentType.other
    quantity: Decimal = Field(default=Decimal("0"), ge=0)
    average_price: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=2)
    current_price: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        decimal_places=2,
        description="Preco informado manualmente. Ignorado quando ha cotacao para o ticker.",
    )
    institution: str | None = Field(default=None, max_length=80)
    notes: str | None = Field(default=None, max_length=500)

    @field_validator("ticker")
    @classmethod
    def _normalize_ticker(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip().upper()
        return cleaned or None


class InvestmentCreate(InvestmentBase):
    pass


class InvestmentUpdate(BaseModel):
    asset: str | None = Field(default=None, min_length=1, max_length=80)
    ticker: str | None = Field(default=None, max_length=16)
    type: InvestmentType | None = None
    quantity: Decimal | None = Field(default=None, ge=0)
    average_price: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    current_price: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    institution: str | None = Field(default=None, max_length=80)
    notes: str | None = Field(default=None, max_length=500)

    @field_validator("ticker")
    @classmethod
    def _normalize_ticker(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip().upper()
        return cleaned or None


class InvestmentRead(InvestmentBase):
    id: uuid.UUID
    invested_amount: Decimal
    current_value: Decimal
    profit: Decimal
    profitability: Decimal
    price_source: PriceSource
    quote_age_seconds: int | None = None
    day_change: Decimal | None = None
    day_change_percent: Decimal | None = None
    long_name: str | None = None
    logo_url: str | None = None
    created_at: datetime


class AllocationSlice(BaseModel):
    type: str
    label: str
    value: Decimal
    percentage: Decimal


class MarketDataStatus(BaseModel):
    """Procedencia dos dados de mercado nesta resposta."""

    provider: str | None
    enabled: bool
    quoted_positions: int
    oldest_quote_age_seconds: int | None
    has_stale_quotes: bool
    crypto_supported: bool


class PortfolioRead(BaseModel):
    invested_amount: Decimal
    current_value: Decimal
    profit: Decimal
    profitability: Decimal
    allocation: list[AllocationSlice]
    positions: list[InvestmentRead]
    market_data: MarketDataStatus


class PortfolioSummary(BaseModel):
    invested_amount: Decimal
    current_value: Decimal
    profit: Decimal
    profitability: Decimal


# -- dados de mercado -------------------------------------------------------


class QuoteRead(BaseModel):
    symbol: str
    price: Decimal
    currency: str
    short_name: str | None = None
    long_name: str | None = None
    change: Decimal | None = None
    change_percent: Decimal | None = None
    day_open: Decimal | None = None
    day_high: Decimal | None = None
    day_low: Decimal | None = None
    previous_close: Decimal | None = None
    volume: int | None = None
    market_cap: int | None = None
    fifty_two_week_low: Decimal | None = None
    fifty_two_week_high: Decimal | None = None
    logo_url: str | None = None
    quoted_at: datetime | None = None
    age_seconds: int
    is_stale: bool


class HistoricalPointRead(BaseModel):
    date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    adjusted_close: Decimal | None = None
    volume: int | None = None


class DividendRead(BaseModel):
    payment_date: date | None
    rate: Decimal
    label: str | None = None
    last_date_prior: date | None = None


class AssetSearchRead(BaseModel):
    symbol: str
    kind: str


class MarketCapabilitiesRead(BaseModel):
    """O que o provedor configurado entrega no plano atual."""

    provider: str | None
    enabled: bool
    quotes: bool
    history: bool
    dividends: bool
    search: bool
    crypto: bool
    notes: dict[str, str]
