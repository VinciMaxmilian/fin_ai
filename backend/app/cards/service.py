from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Sequence

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.cards.models import Card
from app.core.dates import add_months, clamp_day
from app.core.money import ZERO, quantize
from app.core.service import OwnedResourceService
from app.transactions.models import Transaction, TransactionType


@dataclass(frozen=True)
class InvoicePeriod:
    period_start: date
    period_end: date
    closing_date: date
    due_date: date

    def status(self, today: date) -> str:
        if today <= self.closing_date:
            return "open"
        if today <= self.due_date:
            return "closed"
        return "due"


def _next_month(reference: date) -> tuple[int, int]:
    following = add_months(reference.replace(day=1), 1)
    return following.year, following.month


def _previous_month(reference: date) -> tuple[int, int]:
    previous = add_months(reference.replace(day=1), -1)
    return previous.year, previous.month


def invoice_period_for(card: Card, reference: date) -> InvoicePeriod:
    """Fatura em que cai uma compra feita em `reference`.

    Uma compra feita depois do fechamento entra na fatura seguinte, que e como
    as operadoras trabalham.
    """
    closing_this_month = clamp_day(reference.year, reference.month, card.closing_day)
    if reference <= closing_this_month:
        closing = closing_this_month
    else:
        year, month = _next_month(reference)
        closing = clamp_day(year, month, card.closing_day)

    previous_year, previous_month = _previous_month(closing)
    previous_closing = clamp_day(previous_year, previous_month, card.closing_day)
    period_start = previous_closing + timedelta(days=1)

    # O vencimento cai no mesmo mes do fechamento apenas quando o dia de
    # vencimento vem depois do dia de fechamento.
    if card.due_day > card.closing_day:
        due_date = clamp_day(closing.year, closing.month, card.due_day)
    else:
        following = add_months(closing.replace(day=1), 1)
        due_date = clamp_day(following.year, following.month, card.due_day)

    return InvoicePeriod(
        period_start=period_start,
        period_end=closing,
        closing_date=closing,
        due_date=due_date,
    )


class CardService(OwnedResourceService[Card]):
    model = Card
    label = "Cartao"

    def __init__(self, db: Session, user_id: uuid.UUID) -> None:
        super().__init__(db, user_id)
        # Carregados sob demanda e reaproveitados por toda a requisicao. O
        # servico vive uma requisicao so, entao nao ha risco de servir dado
        # velho -- e `invalidate()` cobre o caso de escrita no meio do caminho.
        self._ledger_cache: dict[uuid.UUID, list[tuple[date, Decimal]]] | None = None
        self._cards_cache: dict[bool, Sequence[Card]] = {}

    def list_cards(self, *, include_archived: bool = False) -> Sequence[Card]:
        if include_archived in self._cards_cache:
            return self._cards_cache[include_archived]

        stmt = self.scoped()
        if not include_archived:
            stmt = stmt.where(Card.is_archived.is_(False))
        cards = self.db.execute(stmt.order_by(Card.name)).scalars().all()
        self._cards_cache[include_archived] = cards
        return cards

    # -- faturas -----------------------------------------------------------
    def invoice(self, card: Card, reference: date | None = None) -> dict:
        reference = reference or date.today()
        period = invoice_period_for(card, reference)
        total, count = self._invoice_totals(card.id, period)
        return {
            "card_id": card.id,
            "period_start": period.period_start,
            "period_end": period.period_end,
            "closing_date": period.closing_date,
            "due_date": period.due_date,
            "total": total,
            "transactions_count": count,
            "status": period.status(date.today()),
        }

    def upcoming_invoices(self, card: Card, months: int = 6) -> list[dict]:
        """Fatura atual e as proximas, ja considerando parcelas futuras."""
        invoices: list[dict] = []
        cursor = date.today()
        for _ in range(months):
            invoice = self.invoice(card, cursor)
            invoices.append(invoice)
            cursor = invoice["closing_date"] + timedelta(days=1)
        return invoices

    # -- livro de compras ---------------------------------------------------
    def _ledger(self) -> dict[uuid.UUID, list[tuple[date, Decimal]]]:
        """Todas as compras no credito do usuario, em UMA consulta.

        Antes, cada fatura e cada calculo de limite disparava a propria
        consulta: o dashboard chegava a 49 idas ao banco, 24 delas identicas.
        Com o banco a ~180 ms de distancia, isso custava 10 segundos.

        Carregar o livro inteiro de uma vez e computar em memoria troca N idas
        por uma. O volume e modesto (tres numeros por compra), e o ganho de
        latencia nao tem comparacao.
        """
        if self._ledger_cache is not None:
            return self._ledger_cache

        rows = self.db.execute(
            select(Transaction.card_id, Transaction.date, Transaction.amount).where(
                Transaction.user_id == self.user_id,
                Transaction.card_id.is_not(None),
                Transaction.type == TransactionType.expense,
            )
        ).all()

        ledger: dict[uuid.UUID, list[tuple[date, Decimal]]] = defaultdict(list)
        for card_id, when, amount in rows:
            ledger[card_id].append((when, amount))

        self._ledger_cache = ledger
        return ledger

    def invalidate(self) -> None:
        """Descarta o que esta em memoria. Chame apos escrever cartoes ou compras."""
        self._ledger_cache = None
        self._cards_cache = {}

    def _invoice_totals(self, card_id: uuid.UUID, period: InvoicePeriod) -> tuple[Decimal, int]:
        total = ZERO
        count = 0
        for when, amount in self._ledger().get(card_id, ()):
            if period.period_start <= when <= period.period_end:
                total += amount
                count += 1
        return quantize(total), count

    # -- limite ------------------------------------------------------------
    def used_limit(self, card: Card, today: date | None = None) -> Decimal:
        """Quanto do limite esta comprometido.

        Conta a fatura aberta e as parcelas ja lancadas para o futuro. Faturas
        anteriores sao tratadas como pagas, porque esta versao ainda nao
        registra a quitacao da fatura.
        """
        today = today or date.today()
        current = invoice_period_for(card, today)
        total = sum(
            (amount for when, amount in self._ledger().get(card.id, ()) if when >= current.period_start),
            ZERO,
        )
        return quantize(total)

    def to_read(self, card: Card) -> dict:
        used = self.used_limit(card)
        available = quantize(max(card.limit_amount - used, ZERO))
        fields = (
            "id", "name", "bank", "brand", "limit_amount", "closing_day",
            "due_day", "account_id", "color", "is_archived", "created_at",
        )
        payload = {key: getattr(card, key) for key in fields}
        payload["used_limit"] = used
        payload["available_limit"] = available
        payload["current_invoice"] = self.invoice(card)
        return payload

    def delete(self, resource_id: uuid.UUID) -> None:
        """Excluir o cartao remove suas compras (ondelete CASCADE na transacao)."""
        card = self.get(resource_id)
        self.db.delete(card)
        self.db.commit()
