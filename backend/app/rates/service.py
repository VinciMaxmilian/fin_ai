"""Taxas de referencia com cache.

A serie diaria do CDI de um mes fechado nunca muda, entao pode ser guardada por
muito tempo; a do mes corrente ainda recebe pontos novos a cada dia util, e por
isso vence rapido.
"""
from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal

from app.core.cache import get_cache
from app.core.config import settings
from app.rates.base import DailyRate, RateProvider, RateUnavailableError
from app.rates.bcb import BcbProvider

logger = logging.getLogger(__name__)

PROVIDERS: dict[str, type[RateProvider]] = {"bcb": BcbProvider}


def get_rate_provider() -> RateProvider | None:
    provider_class = PROVIDERS.get((settings.rate_provider or "none").strip().lower())
    return provider_class() if provider_class else None


class RateService:
    def __init__(self, provider: RateProvider | None = None) -> None:
        self._provider = provider or get_rate_provider()
        self._cache = get_cache()

    @property
    def is_enabled(self) -> bool:
        return self._provider is not None

    @property
    def provider_name(self) -> str | None:
        return self._provider.name if self._provider else None

    def daily_series(self, start: date, end: date) -> list[DailyRate]:
        """Serie do CDI no intervalo. Devolve vazio se a fonte estiver fora."""
        if self._provider is None or end < start:
            return []

        key = f"cdi:{self._provider.name}:{start.isoformat()}:{end.isoformat()}"
        cached = self._cache.get(key)
        if cached and cached.is_fresh:
            return cached.value

        try:
            series = self._provider.daily_series(start, end)
        except RateUnavailableError as exc:
            logger.warning("CDI indisponivel de %s a %s: %s", start, end, exc)
            # Vencido ainda serve: taxa passada nao muda.
            return cached.value if cached else []

        # Intervalo inteiramente no passado nao recebe pontos novos.
        closed = end < date.today()
        ttl = settings.rate_history_cache_ttl_seconds if closed else settings.rate_cache_ttl_seconds
        self._cache.set(key, series, ttl)
        return series

    def annual_rate(self) -> Decimal | None:
        """Taxa anualizada, so para exibicao. None quando indisponivel."""
        if self._provider is None:
            return None

        key = f"cdi-anual:{self._provider.name}"
        cached = self._cache.get(key)
        if cached and cached.is_fresh:
            return cached.value

        try:
            value = self._provider.annual_rate()
        except RateUnavailableError as exc:
            logger.warning("Taxa anual indisponivel: %s", exc)
            return cached.value if cached else None

        self._cache.set(key, value, settings.rate_cache_ttl_seconds)
        return value
