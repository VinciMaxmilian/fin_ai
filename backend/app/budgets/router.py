from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Query, status

from app.budgets.schemas import BudgetAmountUpdate, BudgetItem, BudgetSummary, BudgetWrite
from app.budgets.service import BudgetService
from app.core.deps import CurrentUser, DbSession

router = APIRouter(prefix="/budgets", tags=["Orcamento"])


@router.get("", response_model=BudgetSummary, summary="Orcamento do mes com o realizado")
def month_summary(
    user: CurrentUser,
    db: DbSession,
    month: date = Query(default_factory=date.today, description="Qualquer dia do mes"),
) -> BudgetSummary:
    return BudgetSummary.model_validate(BudgetService(db, user.id).summary(month))


@router.put(
    "",
    response_model=BudgetItem,
    summary="Define o valor planejado de uma categoria no mes",
)
def upsert_budget(payload: BudgetWrite, user: CurrentUser, db: DbSession) -> BudgetItem:
    service = BudgetService(db, user.id)
    budget = service.upsert(payload.model_dump())
    item = next(row for row in service.list_month(budget.month) if row["id"] == budget.id)
    return BudgetItem.model_validate(item)


@router.post(
    "/copy-previous",
    response_model=BudgetSummary,
    status_code=status.HTTP_201_CREATED,
    summary="Replica o orcamento do mes anterior",
)
def copy_previous(
    user: CurrentUser,
    db: DbSession,
    month: date = Query(default_factory=date.today),
) -> BudgetSummary:
    service = BudgetService(db, user.id)
    service.copy_from_previous(month)
    return BudgetSummary.model_validate(service.summary(month))


@router.patch("/{budget_id}", response_model=BudgetItem)
def update_budget(
    budget_id: uuid.UUID, payload: BudgetAmountUpdate, user: CurrentUser, db: DbSession
) -> BudgetItem:
    service = BudgetService(db, user.id)
    budget = service.update(budget_id, payload.model_dump())
    item = next(row for row in service.list_month(budget.month) if row["id"] == budget.id)
    return BudgetItem.model_validate(item)


@router.delete("/{budget_id}", response_model=None, status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(budget_id: uuid.UUID, user: CurrentUser, db: DbSession) -> None:
    BudgetService(db, user.id).delete(budget_id)
