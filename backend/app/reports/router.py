from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Query

from app.core.dates import month_range
from app.core.deps import CurrentUser, DbSession
from app.reports.schemas import (
    CardSpending,
    CashFlow,
    CategoryBreakdown,
    Dashboard,
    MonthlySeries,
    NetWorthEvolution,
    Overview,
    RecurringSummary,
    UpcomingBill,
)
from app.reports.service import Period, ReportService

router = APIRouter(prefix="/reports", tags=["Relatorios"])


def _range(date_from: date | None, date_to: date | None) -> tuple[date, date]:
    if date_from and date_to:
        return date_from, date_to
    start, end = month_range(date.today())
    return date_from or start, date_to or end


@router.get("/dashboard", response_model=Dashboard, summary="Todos os blocos do dashboard")
def dashboard(
    user: CurrentUser, db: DbSession, period: Period = Query(default="30d")
) -> Dashboard:
    return Dashboard.model_validate(ReportService(db, user.id).dashboard(period))


@router.get("/overview", response_model=Overview, summary="Numeros do topo do dashboard")
def overview(user: CurrentUser, db: DbSession) -> Overview:
    return Overview.model_validate(ReportService(db, user.id).overview())


@router.get("/cash-flow", response_model=CashFlow, summary="Fluxo financeiro no periodo")
def cash_flow(
    user: CurrentUser, db: DbSession, period: Period = Query(default="30d")
) -> CashFlow:
    return CashFlow.model_validate(ReportService(db, user.id).cash_flow(period))


@router.get(
    "/expenses-by-category",
    response_model=CategoryBreakdown,
    summary="Gastos por categoria",
)
def expenses_by_category(
    user: CurrentUser,
    db: DbSession,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    limit: int | None = Query(default=None, ge=1, le=50),
) -> CategoryBreakdown:
    start, end = _range(date_from, date_to)
    return CategoryBreakdown.model_validate(
        ReportService(db, user.id).expenses_by_category(start, end, limit=limit)
    )


@router.get(
    "/upcoming-bills", response_model=list[UpcomingBill], summary="Proximas contas"
)
def upcoming_bills(
    user: CurrentUser, db: DbSession, days: int = Query(default=30, ge=1, le=365)
) -> list[UpcomingBill]:
    rows = ReportService(db, user.id).upcoming_bills(days)
    return [UpcomingBill.model_validate(row) for row in rows]


@router.get(
    "/monthly", response_model=MonthlySeries, summary="Receitas x despesas mes a mes"
)
def monthly(
    user: CurrentUser, db: DbSession, months: int = Query(default=12, ge=1, le=60)
) -> MonthlySeries:
    return MonthlySeries.model_validate(ReportService(db, user.id).monthly_series(months))


@router.get(
    "/net-worth", response_model=NetWorthEvolution, summary="Evolucao do patrimonio"
)
def net_worth(
    user: CurrentUser, db: DbSession, months: int = Query(default=12, ge=1, le=60)
) -> NetWorthEvolution:
    return NetWorthEvolution.model_validate(
        ReportService(db, user.id).net_worth_evolution(months)
    )


@router.get("/card-spending", response_model=CardSpending, summary="Gastos por cartao")
def card_spending(
    user: CurrentUser,
    db: DbSession,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
) -> CardSpending:
    start, end = _range(date_from, date_to)
    return CardSpending.model_validate(ReportService(db, user.id).card_spending(start, end))


@router.get(
    "/recurring", response_model=RecurringSummary, summary="Peso das contas recorrentes"
)
def recurring(user: CurrentUser, db: DbSession) -> RecurringSummary:
    return RecurringSummary.model_validate(ReportService(db, user.id).recurring_summary())
