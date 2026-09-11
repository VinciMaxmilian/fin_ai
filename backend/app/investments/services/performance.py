"""Calculos de desempenho da carteira.

Funcoes puras, sem banco e sem rede: entram numeros, saem numeros. E aqui que
mora a aritmetica da carteira -- nunca no provedor externo, nunca no React.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.core.money import ZERO, percentage, quantize


@dataclass(frozen=True)
class PositionPerformance:
    quantity: Decimal
    average_price: Decimal
    current_price: Decimal
    invested_amount: Decimal
    current_value: Decimal
    profit: Decimal
    profitability: Decimal


def compute_position(
    *, quantity: Decimal, average_price: Decimal, current_price: Decimal | None
) -> PositionPerformance:
    """Desempenho de uma posicao.

    Sem cotacao atual, o preco medio faz o papel dela: o resultado fica zerado,
    que e a verdade -- nao sabemos se subiu ou desceu.

        10 x R$ 32,50 comprado, cotado a R$ 38,00
        investido  = 325,00
        atual      = 380,00
        lucro      =  55,00
        rentab.    =  16,92%
    """
    price = current_price if current_price and current_price > 0 else average_price

    invested = quantize(quantity * average_price)
    current_value = quantize(quantity * price)
    profit = quantize(current_value - invested)

    return PositionPerformance(
        quantity=quantity,
        average_price=quantize(average_price),
        current_price=quantize(price),
        invested_amount=invested,
        current_value=current_value,
        profit=profit,
        profitability=percentage(profit, invested),
    )


def weighted_average_price(
    *,
    current_quantity: Decimal,
    current_average: Decimal,
    added_quantity: Decimal,
    added_price: Decimal,
) -> Decimal:
    """Novo preco medio ao acrescentar unidades a uma posicao existente.

        50 a R$ 30,00 + 50 a R$ 40,00  ->  R$ 35,00
    """
    total_quantity = current_quantity + added_quantity
    if total_quantity <= 0:
        return ZERO

    total_cost = current_quantity * current_average + added_quantity * added_price
    return quantize(total_cost / total_quantity)


def aggregate(positions: list[PositionPerformance]) -> PositionPerformance:
    """Soma as posicoes em um total consolidado da carteira."""
    invested = quantize(sum((item.invested_amount for item in positions), ZERO))
    current_value = quantize(sum((item.current_value for item in positions), ZERO))
    profit = quantize(current_value - invested)

    return PositionPerformance(
        quantity=ZERO,
        average_price=ZERO,
        current_price=ZERO,
        invested_amount=invested,
        current_value=current_value,
        profit=profit,
        profitability=percentage(profit, invested),
    )
