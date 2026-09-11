"""Contrato dos provedores de taxas de referencia.

Separado de `app/investments/providers` de proposito: la sao cotacoes de ativos,
aqui sao indices macroeconomicos (CDI, Selic). Quem consome tambem e diferente
-- contas remuneradas, nao carteira -- e juntar os dois faria um modulo depender
do outro sem motivo.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


class RateUnavailableError(Exception):
    """Nao foi possivel obter a taxa. Nunca deve travar a leitura das contas."""


@dataclass(frozen=True)
class DailyRate:
    """Taxa de um dia util, em percentual.

    `value` e o percentual do dia, nao a fracao: 0.051660 significa 0,05166% ao
    dia util, que e como o Banco Central publica a serie do CDI.
    """

    date: date
    value: Decimal

    @property
    def factor(self) -> Decimal:
        """Fator multiplicativo do dia para 100% do indice."""
        return Decimal(1) + self.value / Decimal(100)


class RateProvider(ABC):
    name: str

    @abstractmethod
    def daily_series(self, start: date, end: date) -> list[DailyRate]:
        """Taxa de cada dia util no intervalo, em ordem cronologica.

        Dias nao uteis simplesmente nao aparecem -- e a ausencia deles que
        define quais dias remuneram.
        """

    @abstractmethod
    def annual_rate(self) -> Decimal:
        """Taxa anualizada mais recente, para exibicao. Ex.: 13.90."""
