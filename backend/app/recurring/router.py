from __future__ import annotations

import uuid
from datetime import date, timedelta

from fastapi import APIRouter, Query, status

from app.core.deps import CurrentUser, DbSession
from app.recurring.schemas import (
    ConfirmOccurrence,
    OccurrenceRead,
    RecurringCreate,
    RecurringRead,
    RecurringUpdate,
)
from app.recurring.service import RecurringService
from app.transactions.schemas import TransactionRead

router = APIRouter(prefix="/recurring", tags=["Contas recorrentes"])


@router.get("", response_model=list[RecurringRead], summary="Lista as regras recorrentes")
def list_rules(
    user: CurrentUser, db: DbSession, only_active: bool = Query(default=False)
) -> list[RecurringRead]:
    rows = RecurringService(db, user.id).list_rules(only_active=only_active)
    return [RecurringRead.model_validate(row) for row in rows]


@router.post("", response_model=RecurringRead, status_code=status.HTTP_201_CREATED)
def create_rule(payload: RecurringCreate, user: CurrentUser, db: DbSession) -> RecurringRead:
    created = RecurringService(db, user.id).create(payload.model_dump())
    return RecurringRead.model_validate(created)


@router.get(
    "/occurrences",
    response_model=list[OccurrenceRead],
    summary="Previsao das proximas ocorrencias",
)
def list_occurrences(
    user: CurrentUser,
    db: DbSession,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
) -> list[OccurrenceRead]:
    start = date_from or date.today()
    end = date_to or (start + timedelta(days=90))
    rows = RecurringService(db, user.id).occurrences(start, end)
    return [OccurrenceRead.model_validate(row.__dict__) for row in rows]


@router.get("/{rule_id}", response_model=RecurringRead)
def read_rule(rule_id: uuid.UUID, user: CurrentUser, db: DbSession) -> RecurringRead:
    return RecurringRead.model_validate(RecurringService(db, user.id).get(rule_id))


@router.patch("/{rule_id}", response_model=RecurringRead)
def update_rule(
    rule_id: uuid.UUID, payload: RecurringUpdate, user: CurrentUser, db: DbSession
) -> RecurringRead:
    data = payload.model_dump(exclude_unset=True)
    return RecurringRead.model_validate(RecurringService(db, user.id).update(rule_id, data))


@router.delete("/{rule_id}", response_model=None, status_code=status.HTTP_204_NO_CONTENT)
def delete_rule(rule_id: uuid.UUID, user: CurrentUser, db: DbSession) -> None:
    RecurringService(db, user.id).delete(rule_id)


@router.post(
    "/{rule_id}/confirm",
    response_model=TransactionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Converte uma ocorrencia prevista em transacao",
)
def confirm_occurrence(
    rule_id: uuid.UUID, payload: ConfirmOccurrence, user: CurrentUser, db: DbSession
) -> TransactionRead:
    created = RecurringService(db, user.id).confirm(rule_id, payload.due_date)
    return TransactionRead.model_validate(created)
