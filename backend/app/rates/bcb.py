"""Series do Banco Central (SGS).

API publica, sem autenticacao e sem limite divulgado. E a fonte oficial do CDI,
entao nao ha motivo para usar um intermediario pago.

Formato da resposta, medido em 11/09/2026:

    GET https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados/ultimos/3?formato=json
    [{"data":"08/09/2026","valor":"0.051660"}, ...]

Series usadas:
    12    CDI ao dia util, em percentual (0.051660 = 0,05166%)
    4389  CDI anualizado, em percentual (13.90)

O `valor` vem como string com virgula decimal ja normalizada em ponto; ainda
assim convertemos via `Decimal(str(...))` porque esse numero vira dinheiro.
"""
from __future__ import annotations

import logging
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

import httpx

from app.core.config import settings
from app.rates.base import DailyRate, RateProvider, RateUnavailableError

logger = logging.getLogger(__name__)

SERIE_CDI_DIARIO = 12
SERIE_CDI_ANUAL = 4389


class BcbProvider(RateProvider):
    name = "bcb"

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout: float | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = (base_url or settings.bcb_base_url).rstrip("/")
        self._timeout = timeout or settings.bcb_timeout_seconds
        # Injetavel para os testes rodarem sem tocar a rede.
        self._client = client

    def _get(self, path: str, params: dict[str, str] | None = None) -> list[dict]:
        client = self._client or httpx.Client(timeout=self._timeout)
        should_close = self._client is None
        try:
            response = client.get(f"{self.base_url}{path}", params=params or {})
        except httpx.HTTPError as exc:
            raise RateUnavailableError("Banco Central nao respondeu.") from exc
        finally:
            if should_close:
                client.close()

        if response.status_code >= 400:
            raise RateUnavailableError(f"Banco Central respondeu {response.status_code}.")

        try:
            payload = response.json()
        except ValueError as exc:
            raise RateUnavailableError("Banco Central devolveu resposta invalida.") from exc

        if not isinstance(payload, list):
            raise RateUnavailableError("Banco Central devolveu formato inesperado.")
        return payload

    def daily_series(self, start: date, end: date) -> list[DailyRate]:
        if end < start:
            return []

        payload = self._get(
            f"/dados/serie/bcdata.sgs.{SERIE_CDI_DIARIO}/dados",
            {
                "formato": "json",
                "dataInicial": start.strftime("%d/%m/%Y"),
                "dataFinal": end.strftime("%d/%m/%Y"),
            },
        )

        rates: list[DailyRate] = []
        for item in payload:
            parsed = _parse_item(item)
            if parsed:
                rates.append(parsed)
        rates.sort(key=lambda rate: rate.date)
        return rates

    def annual_rate(self) -> Decimal:
        payload = self._get(
            f"/dados/serie/bcdata.sgs.{SERIE_CDI_ANUAL}/dados/ultimos/1",
            {"formato": "json"},
        )
        if not payload:
            raise RateUnavailableError("Banco Central nao devolveu a taxa anual.")

        parsed = _parse_item(payload[0])
        if parsed is None:
            raise RateUnavailableError("Taxa anual em formato invalido.")
        return parsed.value


def _parse_item(item: object) -> DailyRate | None:
    """Converte um ponto da serie. Devolve None se o registro vier quebrado."""
    if not isinstance(item, dict):
        return None
    try:
        when = datetime.strptime(str(item["data"]), "%d/%m/%Y").date()
        value = Decimal(str(item["valor"]).replace(",", "."))
    except (KeyError, ValueError, InvalidOperation):
        logger.warning("BCB: ponto da serie ignorado por formato invalido: %r", item)
        return None
    return DailyRate(date=when, value=value)
