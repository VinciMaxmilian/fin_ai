"""Contrato dos provedores de dados de mercado.

O resto da aplicacao conversa apenas com esta interface e com estes objetos de
transferencia. Nenhum servico da carteira conhece brapi, HG Finance ou qualquer
outro fornecedor -- trocar de provedor e escrever uma classe nova e apontar
`MARKET_DATA_PROVIDER` para ela.

Os tipos abaixo usam `Decimal` porque o valor vira dinheiro assim que encosta na
carteira, e float perde centavos.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal


class MarketDataError(Exception):
    """Falha ao obter dado de mercado. Nunca deve derrubar a carteira."""


class ProviderUnavailableError(MarketDataError):
    """Rede, timeout ou erro 5xx: o provedor nao respondeu."""


class SymbolNotFoundError(MarketDataError):
    """O ticker nao existe na base do provedor."""


class FeatureNotAvailableError(MarketDataError):
    """O recurso existe, mas o plano contratado nao da acesso a ele."""


@dataclass(frozen=True)
class Quote:
    symbol: str
    price: Decimal
    currency: str = "BRL"
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


@dataclass(frozen=True)
class HistoricalPoint:
    date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    adjusted_close: Decimal | None = None
    volume: int | None = None


@dataclass(frozen=True)
class Dividend:
    payment_date: date | None
    rate: Decimal
    label: str | None = None
    last_date_prior: date | None = None


@dataclass(frozen=True)
class AssetSearchResult:
    symbol: str
    kind: str = "stock"


@dataclass(frozen=True)
class ProviderCapabilities:
    """O que este provedor, neste plano, realmente entrega.

    Serve para a interface avisar antes de o usuario tentar, em vez de deixar a
    chamada falhar. Ex.: a brapi so libera cripto em plano pago.
    """

    quotes: bool = True
    history: bool = True
    dividends: bool = True
    search: bool = True
    crypto: bool = False
    unsupported_notes: dict[str, str] = field(default_factory=dict)


class MarketDataProvider(ABC):
    """Interface que qualquer fonte de dados de mercado precisa cumprir.

    Os metodos sao sincronos de proposito. O FastAPI executa os endpoints `def`
    em um pool de threads, entao o I/O aqui nao bloqueia o event loop; e o resto
    do projeto (SQLAlchemy) tambem e sincrono. Um provedor async obrigaria os
    endpoints a serem async, e ai a sessao sincrona do banco e que passaria a
    bloquear o loop -- trocaria um problema por outro pior.
    """

    name: str

    @property
    @abstractmethod
    def capabilities(self) -> ProviderCapabilities: ...

    @abstractmethod
    def get_quotes(self, symbols: list[str]) -> dict[str, Quote]:
        """Cotacao de varios tickers. Ausentes simplesmente nao vem no dicionario."""

    @abstractmethod
    def get_history(
        self, symbol: str, *, range_: str = "1mo", interval: str = "1d"
    ) -> list[HistoricalPoint]: ...

    @abstractmethod
    def get_dividends(self, symbol: str) -> list[Dividend]: ...

    @abstractmethod
    def search(self, term: str) -> list[AssetSearchResult]: ...

    def get_quote(self, symbol: str) -> Quote:
        """Conveniencia para um ticker so."""
        quotes = self.get_quotes([symbol])
        quote = quotes.get(symbol.upper())
        if quote is None:
            raise SymbolNotFoundError(f"Ticker {symbol.upper()} nao encontrado.")
        return quote
