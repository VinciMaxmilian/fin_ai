"""Regras de fechamento e vencimento de fatura.

Usa um objeto simples no lugar do modelo do SQLAlchemy: a funcao so precisa dos
dois dias, e assim o teste nao depende de banco.
"""
from dataclasses import dataclass
from datetime import date, timedelta

from app.cards.service import invoice_period_for


@dataclass
class FakeCard:
    closing_day: int
    due_day: int


def test_compra_antes_do_fechamento_entra_na_fatura_do_mes():
    card = FakeCard(closing_day=20, due_day=28)
    period = invoice_period_for(card, date(2026, 3, 10))
    assert period.closing_date == date(2026, 3, 20)
    assert period.due_date == date(2026, 3, 28)
    assert period.period_start == date(2026, 2, 21)


def test_compra_no_dia_do_fechamento_ainda_entra_na_fatura_atual():
    card = FakeCard(closing_day=20, due_day=28)
    period = invoice_period_for(card, date(2026, 3, 20))
    assert period.closing_date == date(2026, 3, 20)


def test_compra_depois_do_fechamento_cai_na_proxima_fatura():
    card = FakeCard(closing_day=20, due_day=28)
    period = invoice_period_for(card, date(2026, 3, 21))
    assert period.closing_date == date(2026, 4, 20)
    assert period.due_date == date(2026, 4, 28)
    assert period.period_start == date(2026, 3, 21)


def test_vencimento_no_mes_seguinte_quando_vem_antes_do_fechamento():
    # Fecha dia 3, vence dia 10: o vencimento e sempre no mes seguinte ao
    # fechamento nao -- aqui 10 > 3, entao cai no mesmo mes.
    card = FakeCard(closing_day=3, due_day=10)
    period = invoice_period_for(card, date(2026, 3, 1))
    assert period.closing_date == date(2026, 3, 3)
    assert period.due_date == date(2026, 3, 10)

    # Fecha dia 28, vence dia 5: o dia 5 so existe no mes seguinte.
    card = FakeCard(closing_day=28, due_day=5)
    period = invoice_period_for(card, date(2026, 3, 10))
    assert period.closing_date == date(2026, 3, 28)
    assert period.due_date == date(2026, 4, 5)


def test_fechamento_dia_31_em_fevereiro():
    card = FakeCard(closing_day=31, due_day=10)
    period = invoice_period_for(card, date(2026, 2, 15))
    assert period.closing_date == date(2026, 2, 28)
    assert period.due_date == date(2026, 3, 10)


def test_periodos_consecutivos_nao_deixam_buraco_nem_sobrepoem():
    card = FakeCard(closing_day=15, due_day=25)
    primeiro = invoice_period_for(card, date(2026, 5, 1))
    dia_seguinte = primeiro.closing_date + timedelta(days=1)
    seguinte = invoice_period_for(card, dia_seguinte)
    # O periodo seguinte comeca exatamente no dia apos o fechamento anterior.
    assert seguinte.period_start == dia_seguinte
    assert seguinte.closing_date > primeiro.closing_date


def test_status_da_fatura():
    card = FakeCard(closing_day=20, due_day=28)
    period = invoice_period_for(card, date(2026, 3, 10))
    assert period.status(date(2026, 3, 10)) == "open"
    assert period.status(date(2026, 3, 25)) == "closed"
    assert period.status(date(2026, 3, 29)) == "due"
