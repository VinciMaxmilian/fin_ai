"""Rendimento de contas remuneradas.

Como o calculo funciona, e por que assim:

O CDI rende **por dia util**, sobre o **saldo do dia**. Uma conta que recebeu um
deposito no dia 20 nao rende sobre ele desde o dia 1. Por isso o calculo caminha
dia a dia: aplica as transacoes daquele dia, e so entao remunera o saldo
resultante.

O fator diario segue a convencao de mercado para "percentual do CDI":

    fator_do_dia = 1 + (CDI_do_dia / 100) x (percentual / 100)

com 100 = 100% do CDI. O rendimento entra no saldo do dia seguinte, ou seja,
compoe -- que e o que os bancos fazem.

Meses fechados viram uma transacao de receita. O mes em curso e apenas
projecao: ainda esta rendendo, e creditar antes do fim faria o saldo divergir do
extrato do banco.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Iterable, Sequence

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.accounts.models import Account, YieldType
from app.core.dates import add_months, month_range, month_start
from app.core.money import ZERO, quantize
from app.rates import RateService
from app.transactions.models import Transaction, TransactionType

# Trava de seguranca: uma conta com data de inicio muito antiga nao deve gerar
# centenas de transacoes de uma vez na primeira leitura.
MAX_MONTHS_PER_RUN = 24


@dataclass(frozen=True)
class YieldProjection:
    """Quanto a conta rendeu num periodo que ainda nao foi creditado."""

    month: date
    amount: Decimal
    business_days: int
    # False enquanto o mes nao fechou: o valor ainda vai crescer.
    is_closed: bool


def _daily_balance_deltas(
    transactions: Sequence[Transaction], account_id: uuid.UUID
) -> dict[date, Decimal]:
    """Efeito liquido de cada dia sobre o saldo da conta."""
    deltas: dict[date, Decimal] = {}
    for transaction in transactions:
        if transaction.card_id is not None:
            # Compra no cartao nao mexe no saldo da conta.
            continue

        delta = ZERO
        if transaction.account_id == account_id:
            if transaction.type is TransactionType.income:
                delta = transaction.amount
            elif transaction.type is TransactionType.expense:
                delta = -transaction.amount
            elif transaction.type is TransactionType.transfer:
                delta = -transaction.amount
        elif transaction.transfer_account_id == account_id:
            if transaction.type is TransactionType.transfer:
                delta = transaction.amount

        if delta:
            deltas[transaction.date] = deltas.get(transaction.date, ZERO) + delta

    return deltas


def accrue(
    *,
    opening_balance: Decimal,
    start: date,
    end: date,
    rate_percent: Decimal,
    daily_rates: dict[date, Decimal],
    deltas: dict[date, Decimal],
) -> tuple[Decimal, int]:
    """Rendimento acumulado no periodo e quantos dias uteis remuneraram.

    `daily_rates` traz o CDI percentual de cada dia util; dias ausentes nao
    remuneram (fim de semana, feriado).
    """
    balance = opening_balance
    accrued = ZERO
    business_days = 0
    multiplier = rate_percent / Decimal(100)

    cursor = start
    while cursor <= end:
        balance += deltas.get(cursor, ZERO)

        cdi = daily_rates.get(cursor)
        # Saldo negativo nao rende: conta no vermelho nao paga juros a voce.
        if cdi is not None and balance > 0:
            earned = balance * (cdi / Decimal(100)) * multiplier
            accrued += earned
            # Compoe: o rendimento do dia entra no saldo do dia seguinte.
            balance += earned
            business_days += 1

        cursor += timedelta(days=1)

    return quantize(accrued), business_days


class YieldService:
    """Calcula e credita o rendimento das contas do usuario."""

    def __init__(
        self,
        db: Session,
        user_id: uuid.UUID,
        rates: RateService | None = None,
    ) -> None:
        self.db = db
        self.user_id = user_id
        # Injetavel: os testes passam um dublê e nao tocam a rede.
        self.rates = rates or RateService()

    # -- consultas auxiliares ----------------------------------------------
    def _yielding_accounts(self) -> Sequence[Account]:
        return (
            self.db.execute(
                select(Account).where(
                    Account.user_id == self.user_id,
                    Account.yield_type != YieldType.none,
                    Account.yield_rate > 0,
                )
            )
            .scalars()
            .all()
        )

    def _transactions_upto(self, account_id: uuid.UUID, end: date) -> Sequence[Transaction]:
        return (
            self.db.execute(
                select(Transaction).where(
                    Transaction.user_id == self.user_id,
                    Transaction.date <= end,
                    (Transaction.account_id == account_id)
                    | (Transaction.transfer_account_id == account_id),
                )
            )
            .scalars()
            .all()
        )

    @staticmethod
    def _balance_before(
        account: Account, day: date, deltas: dict[date, Decimal]
    ) -> Decimal:
        """Saldo da conta no instante anterior a `day`.

        Recebe os deltas prontos em vez de recalcula-los: ao creditar varios
        meses seguidos, o rendimento ja creditado e acrescentado ao dicionario e
        precisa compor no mes seguinte. Recalcular a partir das transacoes
        carregadas no inicio perderia exatamente esses creditos.
        """
        balance = quantize(account.initial_balance)
        for when, delta in deltas.items():
            if when < day:
                balance += delta
        return balance

    def _first_month(self, account: Account) -> date:
        """Primeiro mes que ainda precisa ser remunerado."""
        if account.last_yield_month:
            return add_months(account.last_yield_month, 1)
        if account.yield_started_on:
            return month_start(account.yield_started_on)
        return month_start(account.created_at.date())

    def _rates_for(self, start: date, end: date) -> dict[date, Decimal]:
        return {rate.date: rate.value for rate in self.rates.daily_series(start, end)}

    # -- projecao -----------------------------------------------------------
    def project(self, account: Account, today: date | None = None) -> YieldProjection | None:
        """Rendimento do mes em curso, ainda nao creditado."""
        today = today or date.today()
        if account.yield_type is YieldType.none or account.yield_rate <= 0:
            return None

        month = month_start(today)
        start, _ = month_range(today)
        if account.yield_started_on and account.yield_started_on > start:
            start = account.yield_started_on
        if start > today:
            return None

        transactions = self._transactions_upto(account.id, today)
        deltas = _daily_balance_deltas(transactions, account.id)
        opening = self._balance_before(account, start, deltas)
        daily_rates = self._rates_for(start, today)
        if not daily_rates:
            return None

        amount, business_days = accrue(
            opening_balance=opening,
            start=start,
            end=today,
            rate_percent=account.yield_rate,
            daily_rates=daily_rates,
            deltas=deltas,
        )
        return YieldProjection(
            month=month, amount=amount, business_days=business_days, is_closed=False
        )

    # -- credito ------------------------------------------------------------
    def settle(self, today: date | None = None) -> list[Transaction]:
        """Credita o rendimento de todos os meses fechados ainda pendentes.

        Chamado na leitura das contas. Silencioso por design: se a fonte da taxa
        estiver fora do ar, nao credita nada e tenta de novo na proxima leitura
        -- a conta continua legivel, apenas sem o rendimento do mes.
        """
        today = today or date.today()
        if not self.rates.is_enabled:
            return []

        # Só meses ja encerrados. O mes corrente ainda esta rendendo.
        last_closed = month_start(add_months(today, -1))
        created: list[Transaction] = []

        for account in self._yielding_accounts():
            created.extend(self._settle_account(account, last_closed))

        return created

    def _settle_account(self, account: Account, last_closed: date) -> list[Transaction]:
        months = list(self._pending_months(account, last_closed))
        if not months:
            return []

        # Uma consulta de taxas cobrindo todos os meses pendentes de uma vez.
        period_start, _ = month_range(months[0])
        _, period_end = month_range(months[-1])
        daily_rates = self._rates_for(period_start, period_end)
        if not daily_rates:
            return []

        transactions = self._transactions_upto(account.id, period_end)
        deltas = _daily_balance_deltas(transactions, account.id)
        created: list[Transaction] = []

        for month in months:
            start, end = month_range(month)
            if account.yield_started_on and account.yield_started_on > start:
                start = account.yield_started_on
            if start > end:
                continue

            opening = self._balance_before(account, start, deltas)
            amount, _ = accrue(
                opening_balance=opening,
                start=start,
                end=end,
                rate_percent=account.yield_rate,
                daily_rates=daily_rates,
                deltas=deltas,
            )

            if amount > ZERO:
                credited = self._credit(account, month, end, amount)
                if credited is None:
                    # Outra requisicao creditou este mes primeiro.
                    return created
                created.append(credited)
                # O rendimento passa a compor o saldo dos meses seguintes.
                deltas[end] = deltas.get(end, ZERO) + amount

            account.last_yield_month = month
            self.db.commit()

        return created

    def _pending_months(self, account: Account, last_closed: date) -> Iterable[date]:
        cursor = self._first_month(account)
        guard = 0
        while cursor <= last_closed and guard < MAX_MONTHS_PER_RUN:
            yield cursor
            cursor = add_months(cursor, 1)
            guard += 1

    def _credit(
        self, account: Account, month: date, when: date, amount: Decimal
    ) -> Transaction | None:
        label = month.strftime("%m/%Y")
        transaction = Transaction(
            user_id=self.user_id,
            type=TransactionType.income,
            amount=amount,
            description=f"Rendimento {label}",
            date=when,
            account_id=account.id,
            yield_month=month,
            notes=f"{account.yield_rate:g}% do CDI",
        )
        self.db.add(transaction)
        try:
            self.db.flush()
        except IntegrityError:
            # O indice unico (account_id, yield_month) barrou uma duplicata.
            self.db.rollback()
            return None
        return transaction
