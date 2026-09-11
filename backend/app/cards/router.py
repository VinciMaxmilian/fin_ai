from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Query, status

from app.cards.schemas import CardCreate, CardRead, CardUpdate, InvoiceRead
from app.cards.service import CardService
from app.core.deps import CurrentUser, DbSession

router = APIRouter(prefix="/cards", tags=["Cartoes"])


@router.get("", response_model=list[CardRead], summary="Lista os cartoes com fatura atual")
def list_cards(
    user: CurrentUser,
    db: DbSession,
    include_archived: bool = Query(default=False),
) -> list[CardRead]:
    service = CardService(db, user.id)
    cards = service.list_cards(include_archived=include_archived)
    return [CardRead.model_validate(service.to_read(card)) for card in cards]


@router.post("", response_model=CardRead, status_code=status.HTTP_201_CREATED)
def create_card(payload: CardCreate, user: CurrentUser, db: DbSession) -> CardRead:
    service = CardService(db, user.id)
    card = service.create(payload.model_dump())
    return CardRead.model_validate(service.to_read(card))


@router.get("/{card_id}", response_model=CardRead)
def read_card(card_id: uuid.UUID, user: CurrentUser, db: DbSession) -> CardRead:
    service = CardService(db, user.id)
    return CardRead.model_validate(service.to_read(service.get(card_id)))


@router.patch("/{card_id}", response_model=CardRead)
def update_card(
    card_id: uuid.UUID, payload: CardUpdate, user: CurrentUser, db: DbSession
) -> CardRead:
    service = CardService(db, user.id)
    card = service.update(card_id, payload.model_dump(exclude_unset=True))
    return CardRead.model_validate(service.to_read(card))


@router.delete("/{card_id}", response_model=None, status_code=status.HTTP_204_NO_CONTENT)
def delete_card(card_id: uuid.UUID, user: CurrentUser, db: DbSession) -> None:
    CardService(db, user.id).delete(card_id)


@router.get(
    "/{card_id}/invoices",
    response_model=list[InvoiceRead],
    summary="Fatura atual e as proximas",
)
def list_invoices(
    card_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
    months: int = Query(default=6, ge=1, le=24),
) -> list[InvoiceRead]:
    service = CardService(db, user.id)
    card = service.get(card_id)
    return [InvoiceRead.model_validate(item) for item in service.upcoming_invoices(card, months)]


@router.get(
    "/{card_id}/invoices/at",
    response_model=InvoiceRead,
    summary="Fatura que contem uma data especifica",
)
def invoice_at(
    card_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
    reference: date = Query(description="Data de referencia"),
) -> InvoiceRead:
    service = CardService(db, user.id)
    card = service.get(card_id)
    return InvoiceRead.model_validate(service.invoice(card, reference))
