"""Aritmetica de datas usada por faturas, recorrencias e parcelamentos."""
from __future__ import annotations

import calendar
from datetime import date, timedelta


def days_in_month(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]


def clamp_day(year: int, month: int, day: int) -> date:
    """Devolve a data mais proxima possivel do dia pedido dentro do mes.

    Regra "todo dia 31" em fevereiro vira o dia 28 (ou 29), e nao um erro.
    """
    return date(year, month, min(day, days_in_month(year, month)))


def add_months(reference: date, months: int) -> date:
    """Soma meses preservando o dia sempre que ele existir no mes destino."""
    total = reference.month - 1 + months
    year = reference.year + total // 12
    month = total % 12 + 1
    return clamp_day(year, month, reference.day)


def month_start(reference: date) -> date:
    return reference.replace(day=1)


def month_end(reference: date) -> date:
    return clamp_day(reference.year, reference.month, 31)


def month_range(reference: date) -> tuple[date, date]:
    """Primeiro e ultimo dia do mes de `reference`, ambos inclusivos."""
    return month_start(reference), month_end(reference)


def iter_months(start: date, end: date):
    """Gera o primeiro dia de cada mes entre `start` e `end`, inclusivo."""
    current = month_start(start)
    limit = month_start(end)
    while current <= limit:
        yield current
        current = add_months(current, 1)


def previous_day(reference: date) -> date:
    return reference - timedelta(days=1)
