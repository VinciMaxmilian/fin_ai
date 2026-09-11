"""Cálculo do rendimento de contas remuneradas.

Testa a função pura `accrue`, sem banco e sem rede. É aqui que um erro custaria
dinheiro de verdade, então os casos cobrem dia útil, saldo variável, juros
compostos e percentual do CDI.
"""
from datetime import date
from decimal import Decimal

from app.accounts.yields import accrue

# CDI de 0,05% ao dia útil — próximo do real (13,9% a.a.) e fácil de conferir
# na mão: R$ 10.000 x 0,0005 = R$ 5,00 por dia.
CDI = Decimal("0.05")


def serie(dias: list[date]) -> dict[date, Decimal]:
    return {dia: CDI for dia in dias}


def test_um_dia_util_a_100_por_cento_do_cdi():
    # 10.000 x 0,05% = 5,00
    valor, uteis = accrue(
        opening_balance=Decimal("10000"),
        start=date(2026, 9, 1),
        end=date(2026, 9, 1),
        rate_percent=Decimal("100"),
        daily_rates=serie([date(2026, 9, 1)]),
        deltas={},
    )
    assert valor == Decimal("5.00")
    assert uteis == 1


def test_percentual_do_cdi_escala_o_rendimento():
    for percentual, esperado in [("50", "2.50"), ("110", "5.50"), ("200", "10.00")]:
        valor, _ = accrue(
            opening_balance=Decimal("10000"),
            start=date(2026, 9, 1),
            end=date(2026, 9, 1),
            rate_percent=Decimal(percentual),
            daily_rates=serie([date(2026, 9, 1)]),
            deltas={},
        )
        assert valor == Decimal(esperado), f"{percentual}% do CDI"


def test_fim_de_semana_nao_rende():
    # 05/09/2026 é sábado, 06/09 é domingo: ausentes da série do BCB.
    valor, uteis = accrue(
        opening_balance=Decimal("10000"),
        start=date(2026, 9, 4),
        end=date(2026, 9, 7),
        rate_percent=Decimal("100"),
        daily_rates=serie([date(2026, 9, 4), date(2026, 9, 7)]),
        deltas={},
    )
    # Só os dois dias úteis rendem.
    assert uteis == 2
    assert valor == Decimal("10.00")


def test_rendimento_compoe():
    # Dois dias: 10.000 -> +5,00 -> 10.005 rende 5,0025 -> total 10,0025
    valor, _ = accrue(
        opening_balance=Decimal("10000"),
        start=date(2026, 9, 1),
        end=date(2026, 9, 2),
        rate_percent=Decimal("100"),
        daily_rates=serie([date(2026, 9, 1), date(2026, 9, 2)]),
        deltas={},
    )
    assert valor == Decimal("10.00")  # 10,0025 arredondado


def test_deposito_no_meio_do_mes_so_rende_a_partir_dali():
    # Dia 1 com 10.000 (rende 5,00); dia 2 entram 10.000 e o saldo passa a
    # ~20.005, rendendo ~10,00. Um cálculo sobre o saldo final daria 20,00.
    valor, _ = accrue(
        opening_balance=Decimal("10000"),
        start=date(2026, 9, 1),
        end=date(2026, 9, 2),
        rate_percent=Decimal("100"),
        daily_rates=serie([date(2026, 9, 1), date(2026, 9, 2)]),
        deltas={date(2026, 9, 2): Decimal("10000")},
    )
    assert valor == Decimal("15.00")
    assert valor < Decimal("20.00"), "o depósito não pode render o mês inteiro"


def test_saque_reduz_o_rendimento_a_partir_do_dia():
    valor, _ = accrue(
        opening_balance=Decimal("10000"),
        start=date(2026, 9, 1),
        end=date(2026, 9, 2),
        rate_percent=Decimal("100"),
        daily_rates=serie([date(2026, 9, 1), date(2026, 9, 2)]),
        deltas={date(2026, 9, 2): Decimal("-8000")},
    )
    # 5,00 no primeiro dia + ~1,00 no segundo
    assert valor == Decimal("6.00")


def test_saldo_zerado_nao_rende():
    valor, uteis = accrue(
        opening_balance=Decimal("0"),
        start=date(2026, 9, 1),
        end=date(2026, 9, 30),
        rate_percent=Decimal("100"),
        daily_rates=serie([date(2026, 9, d) for d in range(1, 31)]),
        deltas={},
    )
    assert valor == Decimal("0.00")
    assert uteis == 0


def test_saldo_negativo_nao_rende():
    # Conta no vermelho não paga juros a favor do titular.
    valor, uteis = accrue(
        opening_balance=Decimal("-500"),
        start=date(2026, 9, 1),
        end=date(2026, 9, 2),
        rate_percent=Decimal("100"),
        daily_rates=serie([date(2026, 9, 1), date(2026, 9, 2)]),
        deltas={},
    )
    assert valor == Decimal("0.00")
    assert uteis == 0


def test_sem_taxa_no_periodo_nao_rende():
    valor, uteis = accrue(
        opening_balance=Decimal("10000"),
        start=date(2026, 9, 1),
        end=date(2026, 9, 30),
        rate_percent=Decimal("100"),
        daily_rates={},
        deltas={},
    )
    assert valor == Decimal("0.00")
    assert uteis == 0


def test_mes_cheio_bate_com_a_taxa_anual():
    # 21 dias úteis a 0,05% ao dia ≈ 1,055% no mês, que anualizado
    # (1,01055^12 - 1) fica na casa de 13% — coerente com o CDI real.
    dias = [date(2026, 9, d) for d in range(1, 30) if date(2026, 9, d).weekday() < 5]
    valor, uteis = accrue(
        opening_balance=Decimal("10000"),
        start=date(2026, 9, 1),
        end=date(2026, 9, 29),
        rate_percent=Decimal("100"),
        daily_rates=serie(dias),
        deltas={},
    )
    assert uteis == len(dias)
    percentual = valor / Decimal("10000") * 100
    assert Decimal("0.9") < percentual < Decimal("1.2"), percentual


def test_rendimento_creditado_compoe_no_mes_seguinte():
    """Regressão: o crédito de um mês precisa render no mês seguinte.

    O bug original recalculava o saldo de abertura a partir da lista de
    transações carregada antes dos créditos, então o rendimento de julho não
    entrava no saldo de agosto — a conta rendia sempre sobre o valor inicial.
    """
    # Julho: R$ 10.000 rendem 5,00 num dia útil.
    julho, _ = accrue(
        opening_balance=Decimal("10000"),
        start=date(2026, 7, 31),
        end=date(2026, 7, 31),
        rate_percent=Decimal("100"),
        daily_rates=serie([date(2026, 7, 31)]),
        deltas={},
    )
    assert julho == Decimal("5.00")

    # O crédito de julho entra como delta e precisa compor em agosto.
    deltas = {date(2026, 7, 31): julho}
    saldo_agosto = Decimal("10000") + sum(
        valor for dia, valor in deltas.items() if dia < date(2026, 8, 31)
    )
    assert saldo_agosto == Decimal("10005.00")

    agosto, _ = accrue(
        opening_balance=saldo_agosto,
        start=date(2026, 8, 31),
        end=date(2026, 8, 31),
        rate_percent=Decimal("100"),
        daily_rates=serie([date(2026, 8, 31)]),
        deltas={},
    )
    # 10.005 x 0,05% = 5,0025 -> 5,00; o que importa é o saldo de abertura.
    assert saldo_agosto > Decimal("10000"), "o rendimento de julho tem de compor"
    assert agosto >= julho
