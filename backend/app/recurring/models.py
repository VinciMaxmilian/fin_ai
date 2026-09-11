from __future__ import annotations

import enum
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, Integer, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, Money, Timestamps, UUIDPrimaryKey
from app.transactions.models import TransactionType


class Frequency(str, enum.Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    yearly = "yearly"


class RecurringRule(Base, UUIDPrimaryKey, Timestamps):
    """Receita ou despesa que se repete. As ocorrencias futuras sao previstas
    sob demanda; so viram transacao quando o usuario confirma."""

    __tablename__ = "recurring_rule"
    __table_args__ = (
        CheckConstraint("amount > 0", name="amount_positive"),
        CheckConstraint("day_of_month IS NULL OR day_of_month BETWEEN 1 AND 31",
                        name="day_of_month_range"),
        CheckConstraint("weekday IS NULL OR weekday BETWEEN 0 AND 6", name="weekday_range"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("app_user.id", ondelete="CASCADE"), index=True
    )
    description: Mapped[str] = mapped_column(String(160), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Money, nullable=False)
    type: Mapped[TransactionType] = mapped_column(
        SAEnum(TransactionType, name="transaction_type", native_enum=False, length=16),
        nullable=False,
    )
    frequency: Mapped[Frequency] = mapped_column(
        SAEnum(Frequency, name="recurrence_frequency", native_enum=False, length=16),
        default=Frequency.monthly,
        nullable=False,
    )
    # Usado quando frequency e monthly ou yearly.
    day_of_month: Mapped[int | None] = mapped_column(Integer)
    # 0 = segunda ... 6 = domingo. Usado quando frequency e weekly.
    weekday: Mapped[int | None] = mapped_column(Integer)
    # Usado quando frequency e yearly.
    month_of_year: Mapped[int | None] = mapped_column(Integer)

    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    category_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("category.id", ondelete="SET NULL")
    )
    account_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("account.id", ondelete="CASCADE")
    )
    card_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("card.id", ondelete="CASCADE")
    )
    notes: Mapped[str | None] = mapped_column(String(500))
