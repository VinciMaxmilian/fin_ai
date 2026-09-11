from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, Money, Timestamps, UUIDPrimaryKey


class InstallmentPlan(Base, UUIDPrimaryKey, Timestamps):
    """Compra parcelada. Cada parcela vira uma transacao ligada a este plano."""

    __tablename__ = "installment_plan"
    __table_args__ = (
        CheckConstraint("installments_count >= 1", name="count_positive"),
        CheckConstraint("total_amount > 0", name="total_positive"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("app_user.id", ondelete="CASCADE"), index=True
    )
    description: Mapped[str] = mapped_column(String(160), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Money, nullable=False)
    installments_count: Mapped[int] = mapped_column(Integer, nullable=False)
    first_due_date: Mapped[date] = mapped_column(Date, nullable=False)
    card_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("card.id", ondelete="CASCADE")
    )
    account_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("account.id", ondelete="SET NULL")
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("category.id", ondelete="SET NULL")
    )
    notes: Mapped[str | None] = mapped_column(String(500))
