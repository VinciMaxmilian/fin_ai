from __future__ import annotations

import uuid
from datetime import date
from typing import Sequence

from sqlalchemy import Select, or_, select

from app.accounts.models import Account
from app.cards.models import Card
from app.categories.models import Category
from app.core.dates import add_months
from app.core.errors import NotFoundError, ValidationError
from app.core.money import split_installments
from app.core.pagination import PageParams, paginate
from app.core.service import OwnedResourceService
from app.installments.models import InstallmentPlan
from app.transactions.models import Transaction, TransactionType
from app.transactions.schemas import TransactionCreate, TransactionFilters

SORT_COLUMNS = {
    "date": Transaction.date,
    "amount": Transaction.amount,
    "description": Transaction.description,
    "created_at": Transaction.created_at,
}


class TransactionService(OwnedResourceService[Transaction]):
    model = Transaction
    label = "Transacao"

    # -- leitura -----------------------------------------------------------
    def build_query(self, filters: TransactionFilters) -> Select:
        stmt = self.scoped()

        if filters.search:
            pattern = f"%{filters.search.strip()}%"
            stmt = stmt.where(
                or_(Transaction.description.ilike(pattern), Transaction.notes.ilike(pattern))
            )
        if filters.type:
            stmt = stmt.where(Transaction.type == filters.type)
        if filters.category_id:
            stmt = stmt.where(Transaction.category_id == filters.category_id)
        if filters.account_id:
            stmt = stmt.where(
                or_(
                    Transaction.account_id == filters.account_id,
                    Transaction.transfer_account_id == filters.account_id,
                )
            )
        if filters.card_id:
            stmt = stmt.where(Transaction.card_id == filters.card_id)
        if filters.date_from:
            stmt = stmt.where(Transaction.date >= filters.date_from)
        if filters.date_to:
            stmt = stmt.where(Transaction.date <= filters.date_to)
        if filters.amount_min is not None:
            stmt = stmt.where(Transaction.amount >= filters.amount_min)
        if filters.amount_max is not None:
            stmt = stmt.where(Transaction.amount <= filters.amount_max)

        column = SORT_COLUMNS[filters.sort_by]
        ordering = column.asc() if filters.sort_order == "asc" else column.desc()
        # Desempate estavel para a paginacao nao repetir nem pular registros.
        return stmt.order_by(ordering, Transaction.id.desc())

    def list_page(self, filters: TransactionFilters, params: PageParams):
        return paginate(self.db, self.build_query(filters), params)

    def list_between(self, start: date, end: date) -> Sequence[Transaction]:
        return (
            self.db.execute(
                self.scoped()
                .where(Transaction.date >= start, Transaction.date <= end)
                .order_by(Transaction.date.asc())
            )
            .scalars()
            .all()
        )

    # -- escrita -----------------------------------------------------------
    def create_transaction(self, payload: TransactionCreate) -> list[Transaction]:
        """Cria o lancamento. Devolve uma lista porque parcelamentos geram varias."""
        self._validate_references(payload)

        if payload.installments > 1:
            return self._create_installment_plan(payload)

        data = payload.model_dump(exclude={"installments"})
        transaction = Transaction(user_id=self.user_id, **data)
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        return [transaction]

    def _create_installment_plan(self, payload: TransactionCreate) -> list[Transaction]:
        if payload.type is not TransactionType.expense:
            raise ValidationError("Apenas despesas podem ser parceladas.")

        plan = InstallmentPlan(
            user_id=self.user_id,
            description=payload.description,
            total_amount=payload.amount,
            installments_count=payload.installments,
            first_due_date=payload.date,
            card_id=payload.card_id,
            account_id=payload.account_id,
            category_id=payload.category_id,
            notes=payload.notes,
        )
        self.db.add(plan)
        self.db.flush()

        amounts = split_installments(payload.amount, payload.installments)
        transactions = [
            Transaction(
                user_id=self.user_id,
                type=TransactionType.expense,
                amount=amount,
                description=f"{payload.description} ({number}/{payload.installments})",
                date=add_months(payload.date, number - 1),
                category_id=payload.category_id,
                account_id=payload.account_id,
                card_id=payload.card_id,
                installment_plan_id=plan.id,
                installment_number=number,
                notes=payload.notes,
            )
            for number, amount in enumerate(amounts, start=1)
        ]
        self.db.add_all(transactions)
        self.db.commit()
        for transaction in transactions:
            self.db.refresh(transaction)
        return transactions

    def update_transaction(self, transaction_id: uuid.UUID, data: dict) -> Transaction:
        transaction = self.get(transaction_id)
        merged = {**_as_dict(transaction), **data}
        self._validate_reference_ids(
            category_id=merged.get("category_id"),
            account_id=merged.get("account_id"),
            card_id=merged.get("card_id"),
            transfer_account_id=merged.get("transfer_account_id"),
        )
        for field, value in data.items():
            setattr(transaction, field, value)
        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    # -- validacao ---------------------------------------------------------
    def _validate_references(self, payload: TransactionCreate) -> None:
        self._validate_reference_ids(
            category_id=payload.category_id,
            account_id=payload.account_id,
            card_id=payload.card_id,
            transfer_account_id=payload.transfer_account_id,
        )

    def _validate_reference_ids(
        self,
        *,
        category_id: uuid.UUID | None,
        account_id: uuid.UUID | None,
        card_id: uuid.UUID | None,
        transfer_account_id: uuid.UUID | None,
    ) -> None:
        """Garante que tudo que a transacao referencia pertence ao mesmo usuario."""
        checks = (
            (Category, category_id, "Categoria"),
            (Account, account_id, "Conta"),
            (Card, card_id, "Cartao"),
            (Account, transfer_account_id, "Conta de destino"),
        )
        for model, resource_id, label in checks:
            if resource_id is None:
                continue
            exists = self.db.execute(
                select(model.id).where(
                    model.id == resource_id, model.user_id == self.user_id
                )
            ).first()
            if not exists:
                raise NotFoundError(f"{label} nao encontrada.")


def _as_dict(transaction: Transaction) -> dict:
    return {
        "type": transaction.type,
        "amount": transaction.amount,
        "description": transaction.description,
        "date": transaction.date,
        "category_id": transaction.category_id,
        "account_id": transaction.account_id,
        "card_id": transaction.card_id,
        "transfer_account_id": transaction.transfer_account_id,
    }
