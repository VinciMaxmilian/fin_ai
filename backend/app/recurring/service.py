from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Sequence

from sqlalchemy import select

from app.core.dates import add_months, clamp_day
from app.core.errors import NotFoundError, ValidationError
from app.core.service import OwnedResourceService
from app.recurring.models import Frequency, RecurringRule
from app.transactions.models import Transaction, TransactionType

# Teto de seguranca para nao gerar uma previsao infinita.
MAX_OCCURRENCES = 500


@dataclass(frozen=True)
class Occurrence:
    rule_id: uuid.UUID
    description: str
    amount: Decimal
    type: TransactionType
    due_date: date
    category_id: uuid.UUID | None
    account_id: uuid.UUID | None
    card_id: uuid.UUID | None
    # True quando ja existe uma transacao confirmada para esta data.
    is_settled: bool


def _first_on_or_after(rule: RecurringRule, start: date) -> date:
    """Primeira data valida da regra a partir de `start`."""
    anchor = max(start, rule.start_date)

    if rule.frequency is Frequency.daily:
        return anchor

    if rule.frequency is Frequency.weekly:
        target = rule.weekday if rule.weekday is not None else rule.start_date.weekday()
        delta = (target - anchor.weekday()) % 7
        return anchor + timedelta(days=delta)

    day = rule.day_of_month or rule.start_date.day

    if rule.frequency is Frequency.monthly:
        candidate = clamp_day(anchor.year, anchor.month, day)
        if candidate < anchor:
            following = add_months(anchor.replace(day=1), 1)
            candidate = clamp_day(following.year, following.month, day)
        return candidate

    # yearly
    month = rule.month_of_year or rule.start_date.month
    candidate = clamp_day(anchor.year, month, day)
    if candidate < anchor:
        candidate = clamp_day(anchor.year + 1, month, day)
    return candidate


def _advance(rule: RecurringRule, current: date) -> date:
    if rule.frequency is Frequency.daily:
        return current + timedelta(days=1)
    if rule.frequency is Frequency.weekly:
        return current + timedelta(days=7)
    if rule.frequency is Frequency.monthly:
        following = add_months(current.replace(day=1), 1)
        return clamp_day(following.year, following.month, rule.day_of_month or current.day)
    following = current.replace(year=current.year + 1, day=1)
    return clamp_day(following.year, following.month, rule.day_of_month or current.day)


class RecurringService(OwnedResourceService[RecurringRule]):
    model = RecurringRule
    label = "Conta recorrente"

    def list_rules(self, *, only_active: bool = False) -> Sequence[RecurringRule]:
        stmt = self.scoped()
        if only_active:
            stmt = stmt.where(RecurringRule.is_active.is_(True))
        return self.db.execute(stmt.order_by(RecurringRule.description)).scalars().all()

    def occurrences(
        self, start: date, end: date, *, rules: Sequence[RecurringRule] | None = None
    ) -> list[Occurrence]:
        """Previsao das ocorrencias no intervalo, sem gravar nada no banco."""
        if end < start:
            raise ValidationError("A data final deve ser posterior a inicial.")

        rules = rules if rules is not None else self.list_rules(only_active=True)
        settled = self._settled_dates([rule.id for rule in rules], start, end)

        results: list[Occurrence] = []
        for rule in rules:
            cursor = _first_on_or_after(rule, start)
            guard = 0
            while cursor <= end and guard < MAX_OCCURRENCES:
                guard += 1
                if rule.end_date and cursor > rule.end_date:
                    break
                if cursor >= rule.start_date:
                    results.append(
                        Occurrence(
                            rule_id=rule.id,
                            description=rule.description,
                            amount=rule.amount,
                            type=rule.type,
                            due_date=cursor,
                            category_id=rule.category_id,
                            account_id=rule.account_id,
                            card_id=rule.card_id,
                            is_settled=(rule.id, cursor) in settled,
                        )
                    )
                cursor = _advance(rule, cursor)

        results.sort(key=lambda item: (item.due_date, item.description))
        return results

    def _settled_dates(
        self, rule_ids: Sequence[uuid.UUID], start: date, end: date
    ) -> set[tuple[uuid.UUID, date]]:
        if not rule_ids:
            return set()
        rows = self.db.execute(
            select(Transaction.recurring_rule_id, Transaction.date).where(
                Transaction.user_id == self.user_id,
                Transaction.recurring_rule_id.in_(rule_ids),
                Transaction.date >= start,
                Transaction.date <= end,
            )
        ).all()
        return {(rule_id, day) for rule_id, day in rows}

    def confirm(self, rule_id: uuid.UUID, due_date: date) -> Transaction:
        """Transforma uma ocorrencia prevista em transacao real."""
        rule = self.get(rule_id)

        already = self.db.execute(
            select(Transaction.id).where(
                Transaction.user_id == self.user_id,
                Transaction.recurring_rule_id == rule.id,
                Transaction.date == due_date,
            )
        ).first()
        if already:
            raise ValidationError("Esta ocorrencia ja foi confirmada.")

        valid_dates = {item.due_date for item in self.occurrences(due_date, due_date, rules=[rule])}
        if due_date not in valid_dates:
            raise NotFoundError("Esta data nao corresponde a uma ocorrencia da regra.")

        transaction = Transaction(
            user_id=self.user_id,
            type=rule.type,
            amount=rule.amount,
            description=rule.description,
            date=due_date,
            category_id=rule.category_id,
            account_id=rule.account_id,
            card_id=rule.card_id,
            recurring_rule_id=rule.id,
            notes=rule.notes,
        )
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        return transaction
