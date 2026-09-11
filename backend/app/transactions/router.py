from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.deps import CurrentUser, DbSession
from app.core.pagination import Page, PageParams, page_params
from app.transactions.models import TransactionType
from app.transactions.schemas import (
    SortField,
    SortOrder,
    TransactionCreate,
    TransactionFilters,
    TransactionRead,
    TransactionUpdate,
)
from app.transactions.service import TransactionService

router = APIRouter(prefix="/transactions", tags=["Transacoes"])


def transaction_filters(
    search: str | None = Query(default=None, description="Busca na descricao e nas observacoes"),
    type: TransactionType | None = Query(default=None),
    category_id: uuid.UUID | None = Query(default=None),
    account_id: uuid.UUID | None = Query(default=None),
    card_id: uuid.UUID | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    amount_min: Decimal | None = Query(default=None),
    amount_max: Decimal | None = Query(default=None),
    sort_by: SortField = Query(default="date"),
    sort_order: SortOrder = Query(default="desc"),
) -> TransactionFilters:
    return TransactionFilters(
        search=search,
        type=type,
        category_id=category_id,
        account_id=account_id,
        card_id=card_id,
        date_from=date_from,
        date_to=date_to,
        amount_min=amount_min,
        amount_max=amount_max,
        sort_by=sort_by,
        sort_order=sort_order,
    )


Filters = Annotated[TransactionFilters, Depends(transaction_filters)]
Paging = Annotated[PageParams, Depends(page_params)]


@router.get(
    "",
    response_model=Page[TransactionRead],
    summary="Lista transacoes com filtros, ordenacao e paginacao",
)
def list_transactions(
    user: CurrentUser, db: DbSession, filters: Filters, params: Paging
) -> Page[TransactionRead]:
    rows, total = TransactionService(db, user.id).list_page(filters, params)
    return Page.build([TransactionRead.model_validate(row) for row in rows], total, params)


@router.post(
    "",
    response_model=list[TransactionRead],
    status_code=status.HTTP_201_CREATED,
    summary="Cria um lancamento (varios quando parcelado)",
)
def create_transaction(
    payload: TransactionCreate, user: CurrentUser, db: DbSession
) -> list[TransactionRead]:
    created = TransactionService(db, user.id).create_transaction(payload)
    return [TransactionRead.model_validate(row) for row in created]


@router.get("/{transaction_id}", response_model=TransactionRead)
def read_transaction(
    transaction_id: uuid.UUID, user: CurrentUser, db: DbSession
) -> TransactionRead:
    return TransactionRead.model_validate(TransactionService(db, user.id).get(transaction_id))


@router.patch("/{transaction_id}", response_model=TransactionRead)
def update_transaction(
    transaction_id: uuid.UUID,
    payload: TransactionUpdate,
    user: CurrentUser,
    db: DbSession,
) -> TransactionRead:
    data = payload.model_dump(exclude_unset=True)
    updated = TransactionService(db, user.id).update_transaction(transaction_id, data)
    return TransactionRead.model_validate(updated)


@router.delete("/{transaction_id}", response_model=None, status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(transaction_id: uuid.UUID, user: CurrentUser, db: DbSession) -> None:
    TransactionService(db, user.id).delete(transaction_id)
