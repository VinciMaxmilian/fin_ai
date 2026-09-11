from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from typing import Iterable, Literal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.accounts.service import AccountService
from app.cards.service import CardService
from app.categories.models import Category
from app.core.dates import add_months, iter_months, month_range, month_start
from app.core.money import ZERO, percentage, quantize
from app.installments.service import InstallmentService
from app.investments.services import InvestmentService
from app.recurring.service import RecurringService
from app.transactions.models import Transaction, TransactionType

Period = Literal["7d", "30d", "3m", "6m", "1y"]

PERIOD_DAYS: dict[Period, int] = {"7d": 7, "30d": 30, "3m": 90, "6m": 180, "1y": 365}
# Abaixo de 60 dias o grafico mostra dias; acima, agrupa por mes.
DAILY_THRESHOLD_DAYS = 60


def resolve_period(period: Period, today: date | None = None) -> tuple[date, date]:
    today = today or date.today()
    days = PERIOD_DAYS[period]
    return today - timedelta(days=days - 1), today


class ReportService:
    """Agregacoes de leitura. Nao escreve nada no banco."""

    def __init__(self, db: Session, user_id: uuid.UUID) -> None:
        self.db = db
        self.user_id = user_id
        # Somas de receita/despesa por dia, cobrindo o maior intervalo ja
        # pedido nesta requisicao. Recortes menores saem daqui sem nova
        # consulta -- e o caso do dashboard, que pede o mes e o periodo.
        self._sums_range: tuple[date, date] | None = None
        self._sums: list[tuple[date, TransactionType, Decimal]] = []
        self.accounts = AccountService(db, user_id)
        self.cards = CardService(db, user_id)
        self.investments = InvestmentService(db, user_id)
        self.recurring = RecurringService(db, user_id)
        self.installments = InstallmentService(db, user_id)

    # -- blocos do dashboard ----------------------------------------------
    def overview(self, today: date | None = None) -> dict:
        today = today or date.today()
        start, end = month_range(today)

        available = self.accounts.total_balance()
        portfolio = self.investments.portfolio(persist_quotes=False)
        open_invoices = quantize(
            sum(
                (self.cards.used_limit(card, today) for card in self.cards.list_cards()),
                ZERO,
            )
        )
        totals = self.totals_between(start, end)

        return {
            "reference_month": month_start(today),
            # Patrimonio = o que esta em conta, mais o investido, menos o que ja
            # foi gasto no cartao e ainda sera debitado.
            "net_worth": quantize(available + portfolio["current_value"] - open_invoices),
            "available_balance": available,
            "invested_amount": portfolio["current_value"],
            "open_invoices": open_invoices,
            "income": totals["income"],
            "expenses": totals["expenses"],
            "balance": quantize(totals["income"] - totals["expenses"]),
        }

    def daily_type_sums(self, start: date, end: date) -> list[tuple[date, TransactionType, Decimal]]:
        """Soma de receitas e despesas por dia no intervalo.

        Transferencias ficam de fora: movem dinheiro entre contas do proprio
        usuario, nao sao receita nem despesa.

        Se o intervalo ja estiver contido no que foi buscado antes nesta
        requisicao, o recorte e feito em memoria.
        """
        if self._sums_range and self._sums_range[0] <= start and end <= self._sums_range[1]:
            return [row for row in self._sums if start <= row[0] <= end]

        # Amplia o intervalo em cache para cobrir o antigo e o novo.
        if self._sums_range:
            start = min(start, self._sums_range[0])
            end = max(end, self._sums_range[1])

        rows = self.db.execute(
            select(Transaction.date, Transaction.type, func.sum(Transaction.amount))
            .where(
                Transaction.user_id == self.user_id,
                Transaction.date >= start,
                Transaction.date <= end,
                Transaction.type != TransactionType.transfer,
            )
            .group_by(Transaction.date, Transaction.type)
        ).all()

        self._sums = [(day, tx_type, quantize(total)) for day, tx_type, total in rows]
        self._sums_range = (start, end)
        return self._sums

    def totals_between(self, start: date, end: date) -> dict[str, Decimal]:
        income = ZERO
        expenses = ZERO
        for _, tx_type, total in self.daily_type_sums(start, end):
            if tx_type == TransactionType.income:
                income += total
            else:
                expenses += total
        return {"income": quantize(income), "expenses": quantize(expenses)}

    def cash_flow(self, period: Period = "30d", today: date | None = None) -> dict:
        """Serie de receitas, despesas e saldo ao longo do periodo."""
        today = today or date.today()
        start, end = resolve_period(period, today)
        span = (end - start).days + 1
        granularity = "day" if span <= DAILY_THRESHOLD_DAYS else "month"

        income: dict[date, Decimal] = defaultdict(lambda: ZERO)
        expenses: dict[date, Decimal] = defaultdict(lambda: ZERO)
        for day, tx_type, total in self.daily_type_sums(start, end):
            bucket = day if granularity == "day" else month_start(day)
            if tx_type == TransactionType.income:
                income[bucket] += total
            else:
                expenses[bucket] += total

        buckets = list(self._buckets(start, end, granularity))
        points = []
        for bucket in buckets:
            bucket_income = quantize(income[bucket])
            bucket_expenses = quantize(expenses[bucket])
            points.append(
                {
                    "date": bucket,
                    "income": bucket_income,
                    "expenses": bucket_expenses,
                    "balance": quantize(bucket_income - bucket_expenses),
                }
            )

        total_income = quantize(sum((p["income"] for p in points), ZERO))
        total_expenses = quantize(sum((p["expenses"] for p in points), ZERO))
        return {
            "period": period,
            "granularity": granularity,
            "start_date": start,
            "end_date": end,
            "total_income": total_income,
            "total_expenses": total_expenses,
            "total_balance": quantize(total_income - total_expenses),
            "points": points,
        }

    @staticmethod
    def _buckets(start: date, end: date, granularity: str) -> Iterable[date]:
        if granularity == "day":
            cursor = start
            while cursor <= end:
                yield cursor
                cursor += timedelta(days=1)
        else:
            yield from iter_months(start, end)

    def expenses_by_category(
        self, start: date, end: date, *, limit: int | None = None
    ) -> dict:
        rows = self.db.execute(
            select(
                Transaction.category_id,
                Category.name,
                Category.color,
                Category.icon,
                func.sum(Transaction.amount),
            )
            .join(Category, Category.id == Transaction.category_id, isouter=True)
            .where(
                Transaction.user_id == self.user_id,
                Transaction.type == TransactionType.expense,
                Transaction.date >= start,
                Transaction.date <= end,
            )
            .group_by(Transaction.category_id, Category.name, Category.color, Category.icon)
        ).all()

        total = quantize(sum((quantize(row[4]) for row in rows), ZERO))
        items = [
            {
                "category_id": row[0],
                "name": row[1] or "Sem categoria",
                "color": row[2] or "#8E8E93",
                "icon": row[3] or "tag",
                "amount": quantize(row[4]),
                "percentage": percentage(quantize(row[4]), total),
            }
            for row in rows
        ]
        items.sort(key=lambda item: item["amount"], reverse=True)

        if limit is not None and len(items) > limit:
            head, tail = items[:limit], items[limit:]
            rest = quantize(sum((item["amount"] for item in tail), ZERO))
            head.append(
                {
                    "category_id": None,
                    "name": "Outros",
                    "color": "#8E8E93",
                    "icon": "ellipsis",
                    "amount": rest,
                    "percentage": percentage(rest, total),
                }
            )
            items = head

        return {"start_date": start, "end_date": end, "total": total, "items": items}

    def upcoming_bills(self, days: int = 30, today: date | None = None) -> list[dict]:
        """Proximos compromissos: recorrencias previstas e faturas de cartao."""
        today = today or date.today()
        horizon = today + timedelta(days=days)
        bills: list[dict] = []

        for occurrence in self.recurring.occurrences(today, horizon):
            if occurrence.type is TransactionType.income or occurrence.is_settled:
                continue
            bills.append(
                {
                    "kind": "recurring",
                    "reference_id": occurrence.rule_id,
                    "description": occurrence.description,
                    "amount": quantize(occurrence.amount),
                    "due_date": occurrence.due_date,
                }
            )

        for card in self.cards.list_cards():
            for invoice in self.cards.upcoming_invoices(card, months=3):
                if invoice["total"] <= 0:
                    continue
                if today <= invoice["due_date"] <= horizon:
                    bills.append(
                        {
                            "kind": "card_invoice",
                            "reference_id": card.id,
                            "description": f"Fatura {card.name}",
                            "amount": invoice["total"],
                            "due_date": invoice["due_date"],
                        }
                    )

        bills.sort(key=lambda bill: (bill["due_date"], bill["description"]))
        return bills

    def dashboard(self, period: Period = "30d", today: date | None = None) -> dict:
        today = today or date.today()
        start, end = month_range(today)
        return {
            "overview": self.overview(today),
            "cash_flow": self.cash_flow(period, today),
            "expenses_by_category": self.expenses_by_category(start, end, limit=6),
            "upcoming_bills": self.upcoming_bills(30, today),
            "cards": [self.cards.to_read(card) for card in self.cards.list_cards()],
        }

    # -- relatorios --------------------------------------------------------
    def monthly_series(self, months: int = 12, today: date | None = None) -> dict:
        """Receitas x despesas mes a mes, com o saldo acumulado."""
        today = today or date.today()
        start = month_start(add_months(today, -(months - 1)))
        _, end = month_range(today)

        rows = self.db.execute(
            select(Transaction.date, Transaction.type, func.sum(Transaction.amount))
            .where(
                Transaction.user_id == self.user_id,
                Transaction.date >= start,
                Transaction.date <= end,
                Transaction.type != TransactionType.transfer,
            )
            .group_by(Transaction.date, Transaction.type)
        ).all()

        income: dict[date, Decimal] = defaultdict(lambda: ZERO)
        expenses: dict[date, Decimal] = defaultdict(lambda: ZERO)
        for day, tx_type, total in rows:
            bucket = month_start(day)
            if tx_type == TransactionType.income:
                income[bucket] += quantize(total)
            else:
                expenses[bucket] += quantize(total)

        points = []
        cumulative = ZERO
        for bucket in iter_months(start, end):
            bucket_income = quantize(income[bucket])
            bucket_expenses = quantize(expenses[bucket])
            balance = quantize(bucket_income - bucket_expenses)
            cumulative = quantize(cumulative + balance)
            points.append(
                {
                    "month": bucket,
                    "income": bucket_income,
                    "expenses": bucket_expenses,
                    "balance": balance,
                    "cumulative_balance": cumulative,
                }
            )
        return {"start_date": start, "end_date": end, "points": points}

    def net_worth_evolution(self, months: int = 12, today: date | None = None) -> dict:
        """Patrimonio ao fim de cada mes, reconstruido a partir do saldo atual.

        Os investimentos entram pelo valor de hoje, porque esta versao nao
        guarda historico de cotacoes.
        """
        today = today or date.today()
        series = self.monthly_series(months, today)["points"]
        current = self.accounts.total_balance()
        invested = self.investments.portfolio()["current_value"]

        # Caminha de tras para frente removendo o resultado de cada mes.
        balances: list[tuple[date, Decimal]] = []
        running = current
        for point in reversed(series):
            balances.append((point["month"], quantize(running)))
            running = quantize(running - point["balance"])
        balances.reverse()

        return {
            "points": [
                {
                    "month": month,
                    "accounts_balance": balance,
                    "invested_amount": invested,
                    "net_worth": quantize(balance + invested),
                }
                for month, balance in balances
            ]
        }

    def card_spending(self, start: date, end: date) -> dict:
        rows = self.db.execute(
            select(Transaction.card_id, func.sum(Transaction.amount))
            .where(
                Transaction.user_id == self.user_id,
                Transaction.type == TransactionType.expense,
                Transaction.card_id.is_not(None),
                Transaction.date >= start,
                Transaction.date <= end,
            )
            .group_by(Transaction.card_id)
        ).all()

        totals = {card_id: quantize(total) for card_id, total in rows}
        grand_total = quantize(sum(totals.values(), ZERO))
        items = [
            {
                "card_id": card.id,
                "name": card.name,
                "color": card.color,
                "amount": totals.get(card.id, ZERO),
                "percentage": percentage(totals.get(card.id, ZERO), grand_total),
            }
            for card in self.cards.list_cards()
        ]
        items.sort(key=lambda item: item["amount"], reverse=True)
        return {"start_date": start, "end_date": end, "total": grand_total, "items": items}

    def recurring_summary(self, today: date | None = None) -> dict:
        """Peso mensal das contas recorrentes."""
        today = today or date.today()
        start, end = month_range(today)
        occurrences = self.recurring.occurrences(start, end)

        income = quantize(
            sum(
                (o.amount for o in occurrences if o.type is TransactionType.income),
                ZERO,
            )
        )
        expenses = quantize(
            sum(
                (o.amount for o in occurrences if o.type is TransactionType.expense),
                ZERO,
            )
        )
        return {
            "month": month_start(today),
            "recurring_income": income,
            "recurring_expenses": expenses,
            "net": quantize(income - expenses),
            "items": [
                {
                    "rule_id": o.rule_id,
                    "description": o.description,
                    "amount": quantize(o.amount),
                    "type": o.type,
                    "due_date": o.due_date,
                    "is_settled": o.is_settled,
                }
                for o in occurrences
            ],
        }
