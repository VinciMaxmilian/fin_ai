"""Dados de mercado com cache e tolerancia a falha do provedor.

Regra que orienta este arquivo: **a carteira do usuario nunca depende da API
externa**. Se o provedor cair, devolvemos a ultima cotacao conhecida marcada
como desatualizada; se nao houver nenhuma, devolvemos nada e a carteira segue
funcionando com o preco que o usuario informou.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date

from app.core.cache import get_cache
from app.core.config import settings
from app.investments.providers import get_market_data_provider
from app.investments.providers.base import (
    AssetSearchResult,
    Dividend,
    FeatureNotAvailableError,
    HistoricalPoint,
    MarketDataError,
    ProviderCapabilities,
    Quote,
    SymbolNotFoundError,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class QuoteResult:
    """Cotacao mais a procedencia dela, que a interface precisa mostrar."""

    quote: Quote
    # Quantos segundos se passaram desde que o dado foi buscado.
    age_seconds: float
    # True quando o cache venceu e o provedor nao respondeu para renovar.
    is_stale: bool


class MarketDataService:
    """Fachada de dados de mercado usada pelo resto do backend."""

    def __init__(self) -> None:
        self._provider = get_market_data_provider()
        self._cache = get_cache()

    @property
    def is_enabled(self) -> bool:
        return self._provider is not None

    @property
    def provider_name(self) -> str | None:
        return self._provider.name if self._provider else None

    @property
    def capabilities(self) -> ProviderCapabilities | None:
        return self._provider.capabilities if self._provider else None

    # -- cotacoes -----------------------------------------------------------
    def get_quotes(self, symbols: list[str]) -> dict[str, QuoteResult]:
        """Cotacao de varios tickers, buscando no provedor so o que falta.

        Nunca levanta excecao: falha de rede vira ausencia de dado, e quem
        chama decide o que exibir.
        """
        wanted = {
            symbol.strip().upper() for symbol in symbols if symbol and symbol.strip()
        }
        if not wanted or self._provider is None:
            return {}

        results: dict[str, QuoteResult] = {}
        missing: list[str] = []
        stale_fallback: dict[str, QuoteResult] = {}

        for symbol in wanted:
            entry = self._cache.get(self._quote_key(symbol))
            if entry is None:
                missing.append(symbol)
                continue
            if entry.is_fresh:
                results[symbol] = QuoteResult(
                    quote=entry.value, age_seconds=entry.age_seconds, is_stale=False
                )
                continue
            # Venceu: tenta renovar, mas guarda o valor antigo como rede de
            # seguranca caso o provedor esteja fora.
            missing.append(symbol)
            if entry.age_seconds <= settings.quote_stale_max_age_seconds:
                stale_fallback[symbol] = QuoteResult(
                    quote=entry.value, age_seconds=entry.age_seconds, is_stale=True
                )

        if missing:
            try:
                fetched = self._provider.get_quotes(missing)
            except MarketDataError as exc:
                logger.warning("Cotacoes indisponiveis para %s: %s", missing, exc)
                fetched = {}

            for symbol, quote in fetched.items():
                self._cache.set(
                    self._quote_key(symbol), quote, settings.quote_cache_ttl_seconds
                )
                results[symbol] = QuoteResult(quote=quote, age_seconds=0.0, is_stale=False)

            # O que o provedor nao devolveu cai no valor antigo, se existir.
            for symbol, fallback in stale_fallback.items():
                results.setdefault(symbol, fallback)

        return results

    def get_quote(self, symbol: str) -> QuoteResult | None:
        return self.get_quotes([symbol]).get(symbol.strip().upper())

    # -- historico ----------------------------------------------------------
    def get_history(
        self, symbol: str, *, range_: str = "1mo", interval: str = "1d"
    ) -> list[HistoricalPoint]:
        if self._provider is None:
            return []

        key = f"history:{self._provider.name}:{symbol.upper()}:{range_}:{interval}"
        cached = self._cache.get(key)
        if cached and cached.is_fresh:
            return cached.value

        try:
            points = self._provider.get_history(symbol, range_=range_, interval=interval)
        except SymbolNotFoundError:
            raise
        except MarketDataError as exc:
            logger.warning("Historico indisponivel para %s: %s", symbol, exc)
            # Vencido ainda serve: historico muda devagar.
            return cached.value if cached else []

        self._cache.set(key, points, settings.history_cache_ttl_seconds)
        return points

    # -- dividendos ---------------------------------------------------------
    def get_dividends(self, symbol: str, *, since: date | None = None) -> list[Dividend]:
        if self._provider is None:
            return []

        key = f"dividends:{self._provider.name}:{symbol.upper()}"
        cached = self._cache.get(key)
        if cached and cached.is_fresh:
            dividends = cached.value
        else:
            try:
                dividends = self._provider.get_dividends(symbol)
                self._cache.set(key, dividends, settings.dividends_cache_ttl_seconds)
            except SymbolNotFoundError:
                raise
            except MarketDataError as exc:
                logger.warning("Dividendos indisponiveis para %s: %s", symbol, exc)
                dividends = cached.value if cached else []

        if since is None:
            return dividends
        return [
            dividend
            for dividend in dividends
            if dividend.payment_date and dividend.payment_date >= since
        ]

    # -- busca --------------------------------------------------------------
    def search(self, term: str) -> list[AssetSearchResult]:
        if self._provider is None or not term.strip():
            return []

        key = f"search:{self._provider.name}:{term.strip().upper()}"
        cached = self._cache.get(key)
        if cached and cached.is_fresh:
            return cached.value

        try:
            results = self._provider.search(term)
        except FeatureNotAvailableError:
            return []
        except MarketDataError as exc:
            logger.warning("Busca de ticker indisponivel para %r: %s", term, exc)
            return cached.value if cached else []

        self._cache.set(key, results, settings.search_cache_ttl_seconds)
        return results

    def invalidate_quotes(self, symbols: list[str]) -> None:
        """Descarta as cotacoes em cache para forcar uma nova consulta."""
        for symbol in symbols:
            if symbol and symbol.strip():
                self._cache.delete(self._quote_key(symbol.strip()))

    def _quote_key(self, symbol: str) -> str:
        provider = self._provider.name if self._provider else "none"
        return f"quote:{provider}:{symbol.upper()}"
