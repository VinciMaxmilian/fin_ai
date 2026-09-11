from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, Money, Timestamps, UUIDPrimaryKey


class Goal(Base, UUIDPrimaryKey, Timestamps):
    __tablename__ = "goal"
    __table_args__ = (
        CheckConstraint("target_amount > 0", name="target_positive"),
        CheckConstraint("current_amount >= 0", name="current_non_negative"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("app_user.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    target_amount: Mapped[Decimal] = mapped_column(Money, nullable=False)
    current_amount: Mapped[Decimal] = mapped_column(Money, default=Decimal("0"), nullable=False)
    target_date: Mapped[date | None] = mapped_column(Date)
    color: Mapped[str] = mapped_column(String(9), default="#34C759", nullable=False)
    icon: Mapped[str] = mapped_column(String(40), default="target", nullable=False)
    notes: Mapped[str | None] = mapped_column(String(500))
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
