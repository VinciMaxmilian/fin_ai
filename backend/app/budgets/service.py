from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.budgets.models import Budget
from app.categories.models import Category
from app.core.dates import month_range, month_start
from app.core.errors import ConflictError, NotFoundError
from app.core.money import ZERO, percentage, quantize
from app.core.service import OwnedResourceService
from app.transactions.models import Transaction, TransactionType


class BudgetService(OwnedResourceService[Budget]):
    model = Budget
    label = "Orcamento"

    def list_month(self, month: date) -> list[dict]:
        """Orcamentos do mes com o quanto ja foi gasto em cada categoria."""
        reference = month_start(month)
        budgets = (
            self.db.execute(self.scoped().where(Budget.month == reference))
            .scalars()
            .all()
        )
        if not budgets:
            return []

        spent = self.spent_by_category(reference)
        categories = self._categories({budget.category_id for budget in budgets})

        rows = []
        for budget in budgets:
            used = spent.get(budget.category_id, ZERO)
            category = categories.get(budget.category_id)
            rows.append(
                {
                    "id": budget.id,
                    "month": budget.month,
                    "category_id": budget.category_id,
                    "category_name": category.name if category else "Categoria removida",
                    "category_color": category.color if category else "#8E8E93",
                    "category_icon": category.icon if category else "tag",
                    "amount": quantize(budget.amount),
                    "spent": used,
                    "remaining": quantize(budget.amount - used),
                    "used_percentage": percentage(used, budget.amount),
                    "is_exceeded": used > budget.amount,
                }
            )
        rows.sort(key=lambda row: row["used_percentage"], reverse=True)
        return rows

    def summary(self, month: date) -> dict:
        rows = self.list_month(month)
        planned = quantize(sum((row["amount"] for row in rows), ZERO))
        spent = quantize(sum((row["spent"] for row in rows), ZERO))
        return {
            "month": month_start(month),
            "total_planned": planned,
            "total_spent": spent,
            "total_remaining": quantize(planned - spent),
            "used_percentage": percentage(spent, planned),
            "items": rows,
        }

    def spent_by_category(self, month: date) -> dict[uuid.UUID, Decimal]:
        start, end = month_range(month)
        rows = self.db.execute(
            select(Transaction.category_id, func.sum(Transaction.amount))
            .where(
                Transaction.user_id == self.user_id,
                Transaction.type == TransactionType.expense,
                Transaction.date >= start,
                Transaction.date <= end,
                Transaction.category_id.is_not(None),
            )
            .group_by(Transaction.category_id)
        ).all()
        return {category_id: quantize(total) for category_id, total in rows}

    def _categories(self, ids: set[uuid.UUID]) -> dict[uuid.UUID, Category]:
        if not ids:
            return {}
        rows = (
            self.db.execute(
                select(Category).where(
                    Category.id.in_(ids), Category.user_id == self.user_id
                )
            )
            .scalars()
            .all()
        )
        return {category.id: category for category in rows}

    def create(self, data: dict) -> Budget:
        data = {**data, "month": month_start(data["month"])}
        self._ensure_category(data["category_id"])
        try:
            return super().create(data)
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError(
                "Ja existe um orcamento para esta categoria neste mes."
            ) from exc

    def upsert(self, data: dict) -> Budget:
        """Cria ou atualiza o orcamento da categoria no mes informado."""
        reference = month_start(data["month"])
        self._ensure_category(data["category_id"])
        existing = self.db.execute(
            self.scoped().where(
                Budget.month == reference, Budget.category_id == data["category_id"]
            )
        ).scalar_one_or_none()
        if existing is None:
            return super().create({**data, "month": reference})
        existing.amount = data["amount"]
        self.db.commit()
        self.db.refresh(existing)
        return existing

    def copy_from_previous(self, month: date) -> Sequence[Budget]:
        """Replica o orcamento do mes anterior, sem sobrescrever o que ja existe."""
        from app.core.dates import add_months

        reference = month_start(month)
        previous = add_months(reference, -1)

        existing_categories = {
            row for row in self.db.execute(
                select(Budget.category_id).where(
                    Budget.user_id == self.user_id, Budget.month == reference
                )
            ).scalars()
        }
        source = (
            self.db.execute(self.scoped().where(Budget.month == previous)).scalars().all()
        )
        created = [
            Budget(
                user_id=self.user_id,
                month=reference,
                category_id=budget.category_id,
                amount=budget.amount,
            )
            for budget in source
            if budget.category_id not in existing_categories
        ]
        if created:
            self.db.add_all(created)
            self.db.commit()
        return created

    def _ensure_category(self, category_id: uuid.UUID) -> None:
        exists = self.db.execute(
            select(Category.id).where(
                Category.id == category_id, Category.user_id == self.user_id
            )
        ).first()
        if not exists:
            raise NotFoundError("Categoria nao encontrada.")
