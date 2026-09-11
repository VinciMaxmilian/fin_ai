from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Sequence

from app.core.errors import ValidationError
from app.core.money import ZERO, percentage, quantize
from app.core.service import OwnedResourceService
from app.goals.models import Goal


class GoalService(OwnedResourceService[Goal]):
    model = Goal
    label = "Meta"

    def list_goals(self, *, include_archived: bool = False) -> Sequence[Goal]:
        stmt = self.scoped()
        if not include_archived:
            stmt = stmt.where(Goal.is_archived.is_(False))
        return self.db.execute(stmt.order_by(Goal.created_at.desc())).scalars().all()

    def contribute(self, goal_id: uuid.UUID, amount: Decimal) -> Goal:
        """Soma (ou subtrai, com valor negativo) um aporte a meta."""
        goal = self.get(goal_id)
        new_amount = quantize(goal.current_amount + amount)
        if new_amount < 0:
            raise ValidationError("O valor acumulado da meta nao pode ficar negativo.")
        goal.current_amount = new_amount
        self.db.commit()
        self.db.refresh(goal)
        return goal

    def to_read(self, goal: Goal) -> dict:
        remaining = quantize(max(goal.target_amount - goal.current_amount, ZERO))
        fields = (
            "id", "name", "target_amount", "current_amount", "target_date",
            "color", "icon", "notes", "is_archived", "created_at",
        )
        payload = {key: getattr(goal, key) for key in fields}
        payload["progress"] = percentage(goal.current_amount, goal.target_amount)
        payload["remaining"] = remaining
        payload["is_completed"] = goal.current_amount >= goal.target_amount
        return payload
