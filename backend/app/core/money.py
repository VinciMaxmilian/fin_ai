"""Helpers para valores monetarios em Decimal."""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

CENTS = Decimal("0.01")
ZERO = Decimal("0.00")


def quantize(value: Decimal | int | float | str) -> Decimal:
    """Arredonda para 2 casas usando a regra comercial (meio para cima)."""
    return Decimal(str(value)).quantize(CENTS, rounding=ROUND_HALF_UP)


def split_installments(total: Decimal, count: int) -> list[Decimal]:
    """Divide um total em `count` parcelas sem perder centavos.

    A diferenca do arredondamento vai para a primeira parcela, que e a
    convencao usada pelas operadoras de cartao no Brasil.
    """
    if count < 1:
        raise ValueError("O numero de parcelas deve ser pelo menos 1.")
    total = quantize(total)
    base = quantize(total / count)
    parcels = [base] * count
    remainder = total - base * count
    parcels[0] = quantize(parcels[0] + remainder)
    return parcels


def percentage(part: Decimal, whole: Decimal) -> Decimal:
    """Percentual de `part` sobre `whole`, com 2 casas. Zero quando nao aplicavel."""
    if whole == 0:
        return ZERO
    return quantize(part / whole * 100)
