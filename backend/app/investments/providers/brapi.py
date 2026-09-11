"""Provedor de dados de mercado da brapi.dev.

Este e o unico arquivo do projeto que fala HTTP com a brapi. Toda a
particularidade dela -- formato de URL, nome dos campos, formato dos erros,
limites do plano -- fica contida aqui.

Limitacoes medidas na API em 11/09/2026, plano gratuito:

- cotacao, histórico, dividendos e busca de tickers funcionam;
- criptomoedas exigem o plano Startup e devolvem `FEATURE_NOT_AVAILABLE`;
- a cotacao aceita varios tickers separados por virgula, o que evita uma
  chamada por ativo da carteira;
- ticker inexistente devolve 404 com `code: NOT_FOUND`;
- sem token a API ainda responde, porem com limite de requisicoes bem menor.
"""
from __future__ import annotations

import logging
import time
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx

from app.core.config import settings
from app.investments.providers.base import (
    AssetSearchResult,
    Dividend,
    FeatureNotAvailableError,
    HistoricalPoint,
    MarketDataProvider,
    ProviderCapabilities,
    ProviderUnavailableError,
    Quote,
    SymbolNotFoundError,
)

logger = logging.getLogger(__name__)

# Erros transitorios: vale a pena repetir. 4xx nao entra aqui — repetir um
# ticker inexistente so gasta requisicao do limite.
RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def _decimal(value: Any) -> Decimal | None:
    """Converte para Decimal via str, para nao herdar o erro do float."""
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _required_decimal(value: Any) -> Decimal:
    result = _decimal(value)
    if result is None:
        raise ValueError(f"Valor numerico invalido recebido do provedor: {value!r}")
    return result


def _int(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (ValueError, TypeError):
        return None


def _datetime(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _date_from_iso(value: Any) -> date | None:
    parsed = _datetime(value)
    return parsed.date() if parsed else None


def _date_from_epoch(value: Any) -> date | None:
    seconds = _int(value)
    if seconds is None:
        return None
    try:
        return datetime.fromtimestamp(seconds, tz=timezone.utc).date()
    except (OverflowError, OSError, ValueError):
        return None


class BrapiProvider(MarketDataProvider):
    name = "brapi"

    def __init__(
        self,
        *,
        base_url: str | None = None,
        token: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = (base_url or settings.brapi_base_url).rstrip("/")
        self._token = token if token is not None else settings.brapi_token
        self._timeout = timeout or settings.brapi_timeout_seconds
        self._max_retries = (
            max_retries if max_retries is not None else settings.brapi_max_retries
        )
        # Injetavel para os testes rodarem sem tocar a rede.
        self._client = client

    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            quotes=True,
            history=True,
            dividends=True,
            search=True,
            # Confirmado contra a API: o plano gratuito recusa cripto.
            crypto=False,
            unsupported_notes={
                "crypto": "Criptomoedas exigem o plano Startup da brapi. "
                "Cadastre a posicao manualmente e informe o preco atual."
            },
        )

    # -- transporte ---------------------------------------------------------
    def _request(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        query: dict[str, Any] = {k: v for k, v in (params or {}).items() if v is not None}
        if self._token:
            query["token"] = self._token

        url = f"{self.base_url}{path}"
        client = self._client or httpx.Client(timeout=self._timeout)
        should_close = self._client is None

        try:
            last_error: Exception | None = None
            for attempt in range(self._max_retries + 1):
                try:
                    response = client.get(url, params=query)
                except httpx.HTTPError as exc:
                    last_error = exc
                    logger.warning(
                        "brapi: falha de rede em %s (tentativa %s)", path, attempt + 1
                    )
                else:
                    if response.status_code in RETRYABLE_STATUS:
                        last_error = ProviderUnavailableError(
                            f"brapi respondeu {response.status_code}."
                        )
                        logger.warning(
                            "brapi: status %s em %s (tentativa %s)",
                            response.status_code,
                            path,
                            attempt + 1,
                        )
                    else:
                        return self._parse(response)

                if attempt < self._max_retries:
                    # Espera crescente, para nao insistir em um servico caido.
                    time.sleep(0.4 * (2**attempt))

            raise ProviderUnavailableError(
                "Nao foi possivel falar com o provedor de dados de mercado."
            ) from last_error
        finally:
            if should_close:
                client.close()

    def _parse(self, response: httpx.Response) -> dict[str, Any]:
        try:
            payload = response.json()
        except ValueError as exc:
            raise ProviderUnavailableError("O provedor devolveu uma resposta invalida.") from exc

        if not isinstance(payload, dict):
            raise ProviderUnavailableError("O provedor devolveu um formato inesperado.")

        if payload.get("error"):
            code = payload.get("code")
            # A mensagem da brapi e apresentavel e nao contem o token.
            message = str(payload.get("message") or "Erro no provedor de dados.")
            if code == "NOT_FOUND" or response.status_code == 404:
                raise SymbolNotFoundError(message)
            if code == "FEATURE_NOT_AVAILABLE":
                raise FeatureNotAvailableError(message)
            raise ProviderUnavailableError(message)

        if response.status_code >= 400:
            raise ProviderUnavailableError(f"O provedor respondeu {response.status_code}.")

        return payload

    # -- dados --------------------------------------------------------------
    def get_quotes(self, symbols: list[str]) -> dict[str, Quote]:
        wanted = [symbol.strip().upper() for symbol in symbols if symbol and symbol.strip()]
        if not wanted:
            return {}

        quotes: dict[str, Quote] = {}
        size = max(1, settings.brapi_batch_size)

        for start in range(0, len(wanted), size):
            batch = wanted[start : start + size]
            try:
                payload = self._request(f"/quote/{','.join(batch)}")
            except SymbolNotFoundError:
                # O lote inteiro pode cair por causa de um unico ticker ruim.
                # Com mais de um, vale reconsultar em separado para nao perder
                # as cotacoes boas.
                if len(batch) == 1:
                    continue
                for symbol in batch:
                    try:
                        payload = self._request(f"/quote/{symbol}")
                    except SymbolNotFoundError:
                        continue
                    quotes.update(self._quotes_from(payload))
                continue

            quotes.update(self._quotes_from(payload))

        return quotes

    def _quotes_from(self, payload: dict[str, Any]) -> dict[str, Quote]:
        results = payload.get("results")
        if not isinstance(results, list):
            return {}

        quotes: dict[str, Quote] = {}
        for item in results:
            if not isinstance(item, dict):
                continue
            symbol = item.get("symbol")
            price = _decimal(item.get("regularMarketPrice"))
            # Sem ticker ou sem preco o registro nao serve para nada.
            if not symbol or price is None:
                continue
            quotes[str(symbol).upper()] = Quote(
                symbol=str(symbol).upper(),
                price=price,
                currency=str(item.get("currency") or "BRL"),
                short_name=item.get("shortName"),
                long_name=item.get("longName"),
                change=_decimal(item.get("regularMarketChange")),
                change_percent=_decimal(item.get("regularMarketChangePercent")),
                day_open=_decimal(item.get("regularMarketOpen")),
                day_high=_decimal(item.get("regularMarketDayHigh")),
                day_low=_decimal(item.get("regularMarketDayLow")),
                previous_close=_decimal(item.get("regularMarketPreviousClose")),
                volume=_int(item.get("regularMarketVolume")),
                market_cap=_int(item.get("marketCap")),
                fifty_two_week_low=_decimal(item.get("fiftyTwoWeekLow")),
                fifty_two_week_high=_decimal(item.get("fiftyTwoWeekHigh")),
                logo_url=item.get("logourl"),
                quoted_at=_datetime(item.get("regularMarketTime")),
            )
        return quotes

    def get_history(
        self, symbol: str, *, range_: str = "1mo", interval: str = "1d"
    ) -> list[HistoricalPoint]:
        payload = self._request(
            f"/quote/{symbol.strip().upper()}",
            {"range": range_, "interval": interval},
        )
        results = payload.get("results")
        if not isinstance(results, list) or not results:
            return []

        raw = results[0].get("historicalDataPrice")
        if not isinstance(raw, list):
            return []

        points: list[HistoricalPoint] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            when = _date_from_epoch(item.get("date"))
            close = _decimal(item.get("close"))
            if when is None or close is None:
                continue
            points.append(
                HistoricalPoint(
                    date=when,
                    open=_decimal(item.get("open")) or close,
                    high=_decimal(item.get("high")) or close,
                    low=_decimal(item.get("low")) or close,
                    close=close,
                    adjusted_close=_decimal(item.get("adjustedClose")),
                    volume=_int(item.get("volume")),
                )
            )
        points.sort(key=lambda point: point.date)
        return points

    def get_dividends(self, symbol: str) -> list[Dividend]:
        payload = self._request(
            f"/quote/{symbol.strip().upper()}", {"dividends": "true"}
        )
        results = payload.get("results")
        if not isinstance(results, list) or not results:
            return []

        data = results[0].get("dividendsData")
        if not isinstance(data, dict):
            return []

        raw = data.get("cashDividends")
        if not isinstance(raw, list):
            return []

        dividends: list[Dividend] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            rate = _decimal(item.get("rate"))
            if rate is None:
                continue
            dividends.append(
                Dividend(
                    payment_date=_date_from_iso(item.get("paymentDate")),
                    rate=rate,
                    label=item.get("label"),
                    last_date_prior=_date_from_iso(item.get("lastDatePrior")),
                )
            )
        dividends.sort(
            key=lambda item: item.payment_date or date.min, reverse=True
        )
        return dividends

    def search(self, term: str) -> list[AssetSearchResult]:
        cleaned = term.strip().upper()
        if not cleaned:
            return []

        payload = self._request("/available", {"search": cleaned})
        results: list[AssetSearchResult] = []
        for key, kind in (("stocks", "stock"), ("indexes", "index")):
            values = payload.get(key)
            if isinstance(values, list):
                results.extend(
                    AssetSearchResult(symbol=str(value).upper(), kind=kind)
                    for value in values
                    if value
                )
        return results
