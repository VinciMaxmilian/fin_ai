from __future__ import annotations

import uuid
from datetime import date
from typing import Sequence

from sqlalchemy import func, select

from app.core.money import ZERO, quantize
from app.core.service import OwnedResourceService
from app.installments.models import InstallmentPlan
from app.transactions.models import Transaction


class InstallmentService(OwnedResourceService[InstallmentPlan]):
    model = InstallmentPlan
    label = "Parcelamento"

    def list_plans(self, *, only_open: bool = False) -> list[dict]:
        plans = (
            self.db.execute(self.scoped().order_by(InstallmentPlan.first_due_date.desc()))
            .scalars()
            .all()
        )
        rows = [self.to_read(plan) for plan in plans]
        if only_open:
            rows = [row for row in rows if row["remaining_installments"] > 0]
        return rows

    def to_read(self, plan: InstallmentPlan, today: date | None = None) -> dict:
        today = today or date.today()
        paid, paid_amount = self._progress(plan.id, today)
        remaining = max(plan.installments_count - paid, 0)

        fields = (
            "id", "description", "total_amount", "installments_count",
            "first_due_date", "card_id", "account_id", "category_id", "notes",
            "created_at",
        )
        payload = {key: getattr(plan, key) for key in fields}
        payload["paid_installments"] = paid
        payload["remaining_installments"] = remaining
        payload["paid_amount"] = paid_amount
        payload["remaining_amount"] = quantize(plan.total_amount - paid_amount)
        payload["installment_amount"] = quantize(
            plan.total_amount / plan.installments_count
        )
        payload["next_due_date"] = self._next_due_date(plan.id, today)
        payload["is_completed"] = remaining == 0
        return payload

    def _progress(self, plan_id: uuid.UUID, today: date) -> tuple[int, "object"]:
        """Parcelas cuja data ja passou: consideradas quitadas."""
        row = self.db.execute(
            select(
                func.count(Transaction.id),
                func.coalesce(func.sum(Transaction.amount), 0),
            ).where(
                Transaction.user_id == self.user_id,
                Transaction.installment_plan_id == plan_id,
                Transaction.date <= today,
            )
        ).one()
        return int(row[0]), quantize(row[1] or ZERO)

    def _next_due_date(self, plan_id: uuid.UUID, today: date) -> date | None:
        return self.db.execute(
            select(func.min(Transaction.date)).where(
                Transaction.user_id == self.user_id,
                Transaction.installment_plan_id == plan_id,
                Transaction.date > today,
            )
        ).scalar_one()

    def installments_of(self, plan_id: uuid.UUID) -> Sequence[Transaction]:
        self.get(plan_id)  # garante posse
        return (
            self.db.execute(
                select(Transaction)
                .where(
                    Transaction.user_id == self.user_id,
                    Transaction.installment_plan_id == plan_id,
                )
                .order_by(Transaction.installment_number)
            )
            .scalars()
            .all()
        )

    def delete(self, resource_id: uuid.UUID) -> None:
        """Remove o plano; as parcelas caem junto pelo ondelete CASCADE."""
        plan = self.get(resource_id)
        self.db.delete(plan)
        self.db.commit()
