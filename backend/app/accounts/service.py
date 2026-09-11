from __future__ import annotations

import uuid
from collections import defaultdict
from decimal import Decimal
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.accounts.models import Account
from app.core.errors import ConflictError
from app.core.money import ZERO, quantize
from app.core.service import OwnedResourceService
from app.transactions.models import Transaction, TransactionType


class AccountService(OwnedResourceService[Account]):
    model = Account
    label = "Conta"

    def __init__(self, db: Session, user_id: uuid.UUID) -> None:
        super().__init__(db, user_id)
        # Uma requisicao chega a pedir saldos e listas varias vezes (saldo
        # total, lista, resumo). Sem memoizar, cada pedido era uma ida ao banco.
        self._accounts_cache: dict[bool, Sequence[Account]] = {}
        self._balances_cache: dict[uuid.UUID, Decimal] | None = None

    def list_accounts(self, *, include_archived: bool = False) -> Sequence[Account]:
        """Contas do usuario, filtrando as arquivadas em memoria.

        Busca sempre o conjunto completo e filtra aqui: pedir "com arquivadas" e
        "sem arquivadas" na mesma requisicao custava duas idas ao banco para um
        recorte que o Python faz de graca.
        """
        if True not in self._accounts_cache:
            accounts = (
                self.db.execute(self.scoped().order_by(Account.name)).scalars().all()
            )
            self._accounts_cache[True] = accounts
            self._accounts_cache[False] = [a for a in accounts if not a.is_archived]
        return self._accounts_cache[include_archived]

    def invalidate(self) -> None:
        """Descarta o que esta em memoria. Chame apos escrever contas."""
        self._accounts_cache = {}
        self._balances_cache = None

    def balances(self) -> dict[uuid.UUID, Decimal]:
        """Saldo atual de cada conta do usuario.

        Compras no cartao nao entram: elas afetam a fatura, e o saldo da conta
        so muda quando a fatura e paga (uma despesa comum na conta).
        """
        if self._balances_cache is not None:
            return self._balances_cache

        accounts = {
            account.id: quantize(account.initial_balance)
            for account in self.list_accounts(include_archived=True)
        }
        deltas: dict[uuid.UUID, Decimal] = defaultdict(lambda: ZERO)

        movements = self.db.execute(
            select(
                Transaction.account_id,
                Transaction.transfer_account_id,
                Transaction.type,
                func.sum(Transaction.amount),
            )
            .where(
                Transaction.user_id == self.user_id,
                Transaction.card_id.is_(None),
            )
            .group_by(
                Transaction.account_id, Transaction.transfer_account_id, Transaction.type
            )
        ).all()

        for account_id, transfer_account_id, tx_type, total in movements:
            total = quantize(total or 0)
            if tx_type == TransactionType.income and account_id:
                deltas[account_id] += total
            elif tx_type == TransactionType.expense and account_id:
                deltas[account_id] -= total
            elif tx_type == TransactionType.transfer:
                if account_id:
                    deltas[account_id] -= total
                if transfer_account_id:
                    deltas[transfer_account_id] += total

        self._balances_cache = {
            account_id: quantize(initial + deltas[account_id])
            for account_id, initial in accounts.items()
        }
        return self._balances_cache

    def balance_of(self, account_id: uuid.UUID) -> Decimal:
        return self.balances().get(account_id, ZERO)

    def total_balance(self, *, include_archived: bool = False) -> Decimal:
        balances = self.balances()
        if include_archived:
            return quantize(sum(balances.values(), ZERO))
        visible = {account.id for account in self.list_accounts()}
        return quantize(sum((v for k, v in balances.items() if k in visible), ZERO))

    def delete(self, resource_id: uuid.UUID) -> None:
        """Impede a perda silenciosa de historico: contas com movimento sao arquivadas."""
        account = self.get(resource_id)
        has_transactions = self.db.execute(
            select(Transaction.id)
            .where(
                Transaction.user_id == self.user_id,
                (Transaction.account_id == account.id)
                | (Transaction.transfer_account_id == account.id),
            )
            .limit(1)
        ).first()
        if has_transactions:
            raise ConflictError(
                "Esta conta possui transacoes. Arquive-a em vez de excluir para "
                "preservar o historico."
            )
        self.db.delete(account)
        self.db.commit()
