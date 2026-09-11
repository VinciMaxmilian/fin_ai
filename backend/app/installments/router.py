from __future__ import annotations

import uuid

from fastapi import APIRouter, Query, status

from app.core.deps import CurrentUser, DbSession
from app.installments.schemas import InstallmentPlanRead, InstallmentPlanUpdate
from app.installments.service import InstallmentService
from app.transactions.schemas import TransactionRead

router = APIRouter(prefix="/installments", tags=["Parcelamentos"])


@router.get("", response_model=list[InstallmentPlanRead], summary="Lista os parcelamentos")
def list_plans(
    user: CurrentUser, db: DbSession, only_open: bool = Query(default=False)
) -> list[InstallmentPlanRead]:
    rows = InstallmentService(db, user.id).list_plans(only_open=only_open)
    return [InstallmentPlanRead.model_validate(row) for row in rows]


@router.get("/{plan_id}", response_model=InstallmentPlanRead)
def read_plan(plan_id: uuid.UUID, user: CurrentUser, db: DbSession) -> InstallmentPlanRead:
    service = InstallmentService(db, user.id)
    return InstallmentPlanRead.model_validate(service.to_read(service.get(plan_id)))


@router.get(
    "/{plan_id}/transactions",
    response_model=list[TransactionRead],
    summary="Parcelas do plano",
)
def list_plan_transactions(
    plan_id: uuid.UUID, user: CurrentUser, db: DbSession
) -> list[TransactionRead]:
    rows = InstallmentService(db, user.id).installments_of(plan_id)
    return [TransactionRead.model_validate(row) for row in rows]


@router.patch("/{plan_id}", response_model=InstallmentPlanRead)
def update_plan(
    plan_id: uuid.UUID, payload: InstallmentPlanUpdate, user: CurrentUser, db: DbSession
) -> InstallmentPlanRead:
    service = InstallmentService(db, user.id)
    plan = service.update(plan_id, payload.model_dump(exclude_unset=True))
    return InstallmentPlanRead.model_validate(service.to_read(plan))


@router.delete(
    "/{plan_id}",
    response_model=None, status_code=status.HTTP_204_NO_CONTENT,
    summary="Exclui o plano e todas as suas parcelas",
)
def delete_plan(plan_id: uuid.UUID, user: CurrentUser, db: DbSession) -> None:
    InstallmentService(db, user.id).delete(plan_id)
