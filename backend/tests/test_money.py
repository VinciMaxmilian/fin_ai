from decimal import Decimal

import pytest

from app.core.money import percentage, quantize, split_installments


def test_quantize_arredonda_meio_para_cima():
    assert quantize("1.005") == Decimal("1.01")
    assert quantize("2.344") == Decimal("2.34")
    assert quantize(10) == Decimal("10.00")


def test_split_installments_preserva_o_total():
    for total, count in [("4200.00", 12), ("100.00", 3), ("0.05", 2), ("999.99", 7)]:
        parcels = split_installments(Decimal(total), count)
        assert len(parcels) == count
        assert sum(parcels) == Decimal(total), f"{total} em {count}x perdeu centavos"


def test_split_installments_joga_a_sobra_na_primeira_parcela():
    # 100 / 3 = 33,333... -> 33,34 + 33,33 + 33,33
    parcels = split_installments(Decimal("100.00"), 3)
    assert parcels == [Decimal("33.34"), Decimal("33.33"), Decimal("33.33")]


def test_split_installments_divisao_exata():
    parcels = split_installments(Decimal("4200.00"), 12)
    assert parcels == [Decimal("350.00")] * 12


def test_split_installments_recusa_contagem_invalida():
    with pytest.raises(ValueError):
        split_installments(Decimal("10.00"), 0)


def test_percentage_protege_contra_divisao_por_zero():
    assert percentage(Decimal("10"), Decimal("0")) == Decimal("0.00")
    assert percentage(Decimal("620"), Decimal("700")) == Decimal("88.57")
