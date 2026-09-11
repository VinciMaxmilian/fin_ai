from __future__ import annotations

import uuid

from fastapi import APIRouter, Query, status

from app.accounts.models import Account, YieldType
from app.accounts.schemas import (
    AccountCreate,
    AccountRead,
    AccountsSummary,
    AccountUpdate,
    YieldInfo,
)
from app.accounts.service import AccountService
from app.accounts.yields import YieldService
from app.core.deps import CurrentUser, DbSession
from app.rates import RateService

router = APIRouter(prefix="/accounts", tags=["Contas"])

FIELDS = (
    "id", "name", "bank", "type", "initial_balance", "color", "icon",
    "is_archived", "created_at", "yield_type", "yield_rate",
    "yield_started_on", "last_yield_month",
)


def _to_read(
    account: Account,
    balances: dict,
    yield_info: YieldInfo | None = None,
) -> AccountRead:
    payload = {key: getattr(account, key) for key in FIELDS}
    payload["current_balance"] = balances.get(account.id, account.initial_balance)
    payload["yield_info"] = yield_info
    return AccountRead.model_validate(payload)


@router.get("", response_model=AccountsSummary, summary="Lista as contas com saldo atual")
def list_accounts(
    user: CurrentUser,
    db: DbSession,
    include_archived: bool = Query(default=False),
) -> AccountsSummary:
    """Lista as contas e, de passagem, credita rendimentos pendentes.

    O credito acontece aqui de proposito: sem um agendador rodando, o momento
    em que o usuario abre o app e o unico gatilho confiavel. `settle` e
    idempotente (indice unico por conta e mes) e silencioso quando a fonte da
    taxa esta fora do ar, entao a listagem nunca falha por causa disso.
    """
    yields = YieldService(db, user.id)
    yields.settle()

    service = AccountService(db, user.id)
    balances = service.balances()
    accounts = service.list_accounts(include_archived=include_archived)

    rates = RateService()
    annual = rates.annual_rate()

    rows = []
    for account in accounts:
        info = None
        if account.yield_type is not YieldType.none and account.yield_rate > 0:
            projection = yields.project(account)
            if projection:
                info = YieldInfo(
                    projected_amount=projection.amount,
                    projected_month=projection.month,
                    business_days=projection.business_days,
                    last_credited_month=account.last_yield_month,
                    annual_rate=annual,
                )
        rows.append(_to_read(account, balances, info))

    return AccountsSummary(
        total_balance=service.total_balance(include_archived=include_archived),
        accounts=rows,
        cdi_annual_rate=annual,
    )


@router.post("", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def create_account(payload: AccountCreate, user: CurrentUser, db: DbSession) -> AccountRead:
    service = AccountService(db, user.id)
    account = service.create(payload.model_dump())
    return _to_read(account, service.balances())


@router.get("/{account_id}", response_model=AccountRead)
def read_account(account_id: uuid.UUID, user: CurrentUser, db: DbSession) -> AccountRead:
    service = AccountService(db, user.id)
    return _to_read(service.get(account_id), service.balances())


@router.patch("/{account_id}", response_model=AccountRead)
def update_account(
    account_id: uuid.UUID, payload: AccountUpdate, user: CurrentUser, db: DbSession
) -> AccountRead:
    service = AccountService(db, user.id)
    account = service.update(account_id, payload.model_dump(exclude_unset=True))
    return _to_read(account, service.balances())


@router.delete("/{account_id}", response_model=None, status_code=status.HTTP_204_NO_CONTENT)
def delete_account(account_id: uuid.UUID, user: CurrentUser, db: DbSession) -> None:
    AccountService(db, user.id).delete(account_id)
