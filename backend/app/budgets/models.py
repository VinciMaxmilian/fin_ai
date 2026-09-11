from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, Money, Timestamps, UUIDPrimaryKey


class Budget(Base, UUIDPrimaryKey, Timestamps):
    """Limite planejado de gasto para uma categoria em um mes."""

    __tablename__ = "budget"
    __table_args__ = (
        UniqueConstraint("user_id", "month", "category_id", name="uq_budget_user_id_month_category"),
        CheckConstraint("amount >= 0", name="amount_non_negative"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("app_user.id", ondelete="CASCADE"), index=True
    )
    # Sempre o primeiro dia do mes de referencia.
    month: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    category_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("category.id", ondelete="CASCADE"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Money, nullable=False)
