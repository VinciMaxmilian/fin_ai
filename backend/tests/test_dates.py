from datetime import date

from app.core.dates import add_months, clamp_day, iter_months, month_end, month_range


def test_clamp_day_encaixa_no_ultimo_dia_do_mes():
    assert clamp_day(2026, 2, 31) == date(2026, 2, 28)
    assert clamp_day(2024, 2, 31) == date(2024, 2, 29)  # bissexto
    assert clamp_day(2026, 4, 31) == date(2026, 4, 30)
    assert clamp_day(2026, 1, 15) == date(2026, 1, 15)


def test_add_months_preserva_o_dia_quando_existe():
    assert add_months(date(2026, 1, 15), 1) == date(2026, 2, 15)
    assert add_months(date(2026, 1, 15), 12) == date(2027, 1, 15)
    assert add_months(date(2026, 3, 10), -1) == date(2026, 2, 10)


def test_add_months_a_partir_do_dia_31():
    # "Todo dia 31" precisa sobreviver a fevereiro sem estourar.
    assert add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)
    assert add_months(date(2026, 1, 31), 3) == date(2026, 4, 30)


def test_add_months_atravessa_o_ano():
    assert add_months(date(2026, 11, 20), 3) == date(2027, 2, 20)
    assert add_months(date(2026, 1, 20), -2) == date(2025, 11, 20)


def test_month_range_e_month_end():
    assert month_range(date(2026, 2, 10)) == (date(2026, 2, 1), date(2026, 2, 28))
    assert month_end(date(2026, 12, 5)) == date(2026, 12, 31)


def test_iter_months_inclui_as_duas_pontas():
    months = list(iter_months(date(2026, 11, 15), date(2027, 2, 3)))
    assert months == [
        date(2026, 11, 1),
        date(2026, 12, 1),
        date(2027, 1, 1),
        date(2027, 2, 1),
    ]
