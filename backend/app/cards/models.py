from __future__ import annotations

import enum
import uuid
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, Money, Timestamps, UUIDPrimaryKey


class CardBrand(str, enum.Enum):
    visa = "visa"
    mastercard = "mastercard"
    elo = "elo"
    amex = "amex"
    hipercard = "hipercard"
    other = "other"


class Card(Base, UUIDPrimaryKey, Timestamps):
    __tablename__ = "card"
    __table_args__ = (
        CheckConstraint("closing_day BETWEEN 1 AND 31", name="closing_day_range"),
        CheckConstraint("due_day BETWEEN 1 AND 31", name="due_day_range"),
        CheckConstraint("limit_amount >= 0", name="limit_non_negative"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("app_user.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    bank: Mapped[str | None] = mapped_column(String(80))
    brand: Mapped[CardBrand] = mapped_column(
        SAEnum(CardBrand, name="card_brand", native_enum=False, length=16),
        default=CardBrand.other,
        nullable=False,
    )
    limit_amount: Mapped[Decimal] = mapped_column(Money, default=Decimal("0"), nullable=False)
    closing_day: Mapped[int] = mapped_column(Integer, nullable=False)
    due_day: Mapped[int] = mapped_column(Integer, nullable=False)
    # Conta de onde a fatura e debitada.
    account_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("account.id", ondelete="SET NULL")
    )
    color: Mapped[str] = mapped_column(String(9), default="#1C1C1E", nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
