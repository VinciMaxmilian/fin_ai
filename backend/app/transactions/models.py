from __future__ import annotations

import enum
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, Integer, String, text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, Money, Timestamps, UUIDPrimaryKey


class TransactionType(str, enum.Enum):
    income = "income"
    expense = "expense"
    transfer = "transfer"


class Transaction(Base, UUIDPrimaryKey, Timestamps):
    __tablename__ = "transaction"
    __table_args__ = (
        CheckConstraint("amount > 0", name="amount_positive"),
        Index("ix_transaction_user_date", "user_id", "date"),
        Index("ix_transaction_user_card_date", "user_id", "card_id", "date"),
        # Idempotencia do rendimento: duas requisicoes simultaneas nao podem
        # creditar o mesmo mes duas vezes. A garantia vive no banco, nao na
        # aplicacao, porque e onde a corrida realmente acontece.
        Index(
            "uq_transaction_yield_month",
            "account_id",
            "yield_month",
            unique=True,
            postgresql_where=text("yield_month IS NOT NULL"),
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("app_user.id", ondelete="CASCADE"), index=True
    )
    type: Mapped[TransactionType] = mapped_column(
        SAEnum(TransactionType, name="transaction_type", native_enum=False, length=16),
        nullable=False,
    )
    # Sempre positivo. O sinal e dado por `type`, o que evita o erro classico de
    # somar despesas ja negativas duas vezes.
    amount: Mapped[Decimal] = mapped_column(Money, nullable=False)
    description: Mapped[str] = mapped_column(String(160), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    category_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("category.id", ondelete="SET NULL"), index=True
    )
    account_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("account.id", ondelete="CASCADE"), index=True
    )
    card_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("card.id", ondelete="CASCADE"), index=True
    )
    # Conta de destino, usada apenas quando `type` e transfer.
    transfer_account_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("account.id", ondelete="CASCADE")
    )

    installment_plan_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("installment_plan.id", ondelete="CASCADE"), index=True
    )
    installment_number: Mapped[int | None] = mapped_column(Integer)

    # Preenchido quando a transacao nasceu de uma regra recorrente.
    recurring_rule_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("recurring_rule.id", ondelete="SET NULL"), index=True
    )

    # Preenchido quando a transacao e o credito de rendimento de um mes.
    # Guarda o primeiro dia do mes remunerado.
    yield_month: Mapped[date | None] = mapped_column(Date)

    notes: Mapped[str | None] = mapped_column(String(500))

    # selectin: a listagem traz as categorias em uma unica consulta extra
    # por lote, em vez de uma por linha.
    category: Mapped["Category | None"] = relationship(  # noqa: F821
        "Category", lazy="selectin", viewonly=True
    )
