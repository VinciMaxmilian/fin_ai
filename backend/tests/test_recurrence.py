"""Calculo das datas de uma regra recorrente."""
from dataclasses import dataclass
from datetime import date

from app.recurring.models import Frequency
from app.recurring.service import _advance, _first_on_or_after


@dataclass
class FakeRule:
    frequency: Frequency
    start_date: date
    day_of_month: int | None = None
    weekday: int | None = None
    month_of_year: int | None = None


def ocorrencias(rule: FakeRule, start: date, quantidade: int) -> list[date]:
    cursor = _first_on_or_after(rule, start)
    datas = [cursor]
    for _ in range(quantidade - 1):
        cursor = _advance(rule, cursor)
        datas.append(cursor)
    return datas


def test_mensal_todo_dia_5():
    rule = FakeRule(Frequency.monthly, date(2026, 1, 1), day_of_month=5)
    assert ocorrencias(rule, date(2026, 1, 1), 3) == [
        date(2026, 1, 5),
        date(2026, 2, 5),
        date(2026, 3, 5),
    ]


def test_mensal_pula_para_o_mes_seguinte_se_o_dia_ja_passou():
    rule = FakeRule(Frequency.monthly, date(2026, 1, 1), day_of_month=5)
    assert _first_on_or_after(rule, date(2026, 1, 10)) == date(2026, 2, 5)


def test_mensal_dia_31_encaixa_em_fevereiro():
    rule = FakeRule(Frequency.monthly, date(2026, 1, 1), day_of_month=31)
    datas = ocorrencias(rule, date(2026, 1, 1), 4)
    assert datas[0] == date(2026, 1, 31)
    assert datas[1] == date(2026, 2, 28)
    # Depois de encolher para 28, volta ao dia 31 no mes que comporta.
    assert datas[2] == date(2026, 3, 31)
    assert datas[3] == date(2026, 4, 30)


def test_semanal_cai_sempre_no_mesmo_dia_da_semana():
    # 2026-01-01 e uma quinta-feira; weekday=0 significa segunda.
    rule = FakeRule(Frequency.weekly, date(2026, 1, 1), weekday=0)
    datas = ocorrencias(rule, date(2026, 1, 1), 3)
    assert all(d.weekday() == 0 for d in datas)
    assert (datas[1] - datas[0]).days == 7


def test_diario():
    rule = FakeRule(Frequency.daily, date(2026, 1, 1))
    datas = ocorrencias(rule, date(2026, 1, 30), 3)
    assert datas == [date(2026, 1, 30), date(2026, 1, 31), date(2026, 2, 1)]


def test_anual():
    rule = FakeRule(Frequency.yearly, date(2026, 3, 15), day_of_month=15, month_of_year=3)
    assert _first_on_or_after(rule, date(2026, 1, 1)) == date(2026, 3, 15)
    # Depois que a data do ano passa, vai para o ano seguinte.
    assert _first_on_or_after(rule, date(2026, 4, 1)) == date(2027, 3, 15)


def test_nunca_devolve_data_anterior_ao_inicio_da_regra():
    rule = FakeRule(Frequency.monthly, date(2026, 6, 10), day_of_month=10)
    assert _first_on_or_after(rule, date(2026, 1, 1)) == date(2026, 6, 10)
