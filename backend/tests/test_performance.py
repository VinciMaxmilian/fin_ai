"""Calculos da carteira. Nenhuma rede, nenhum banco."""
from decimal import Decimal

from app.investments.services.performance import (
    aggregate,
    compute_position,
    weighted_average_price,
)


def D(value: str) -> Decimal:
    return Decimal(value)


def test_exemplo_da_especificacao():
    # 10 x R$ 32,50 comprado, cotado a R$ 38,00.
    resultado = compute_position(
        quantity=D("10"), average_price=D("32.50"), current_price=D("38.00")
    )
    assert resultado.invested_amount == D("325.00")
    assert resultado.current_value == D("380.00")
    assert resultado.profit == D("55.00")
    assert resultado.profitability == D("16.92")


def test_prejuizo_tem_sinal_negativo():
    resultado = compute_position(
        quantity=D("100"), average_price=D("30.00"), current_price=D("24.00")
    )
    assert resultado.profit == D("-600.00")
    assert resultado.profitability == D("-20.00")


def test_sem_cotacao_usa_o_preco_medio_e_zera_o_resultado():
    # Nao sabemos se subiu ou desceu: inventar um numero seria pior que zero.
    resultado = compute_position(
        quantity=D("10"), average_price=D("32.50"), current_price=None
    )
    assert resultado.current_price == D("32.50")
    assert resultado.current_value == D("325.00")
    assert resultado.profit == D("0.00")
    assert resultado.profitability == D("0.00")


def test_cotacao_zero_e_tratada_como_ausente():
    resultado = compute_position(
        quantity=D("10"), average_price=D("32.50"), current_price=D("0")
    )
    assert resultado.current_price == D("32.50")


def test_quantidade_fracionada():
    resultado = compute_position(
        quantity=D("0.00512345"), average_price=D("380000.00"), current_price=D("400000.00")
    )
    assert resultado.invested_amount == D("1946.91")
    assert resultado.current_value == D("2049.38")


def test_posicao_zerada_nao_divide_por_zero():
    resultado = compute_position(
        quantity=D("0"), average_price=D("0"), current_price=D("10.00")
    )
    assert resultado.invested_amount == D("0.00")
    assert resultado.profitability == D("0.00")


def test_preco_medio_ponderado():
    # 50 a 30 + 50 a 40 = 35
    assert weighted_average_price(
        current_quantity=D("50"),
        current_average=D("30.00"),
        added_quantity=D("50"),
        added_price=D("40.00"),
    ) == D("35.00")

    # Compra desigual puxa a media para o lado do maior volume.
    assert weighted_average_price(
        current_quantity=D("100"),
        current_average=D("20.00"),
        added_quantity=D("10"),
        added_price=D("40.00"),
    ) == D("21.82")


def test_preco_medio_a_partir_de_posicao_vazia():
    assert weighted_average_price(
        current_quantity=D("0"),
        current_average=D("0"),
        added_quantity=D("10"),
        added_price=D("32.50"),
    ) == D("32.50")


def test_agregado_soma_as_posicoes():
    posicoes = [
        compute_position(quantity=D("10"), average_price=D("32.50"), current_price=D("38.00")),
        compute_position(quantity=D("5"), average_price=D("100.00"), current_price=D("90.00")),
    ]
    total = aggregate(posicoes)
    assert total.invested_amount == D("825.00")
    assert total.current_value == D("830.00")
    assert total.profit == D("5.00")
    assert total.profitability == D("0.61")


def test_agregado_de_carteira_vazia():
    total = aggregate([])
    assert total.invested_amount == D("0.00")
    assert total.profitability == D("0.00")
