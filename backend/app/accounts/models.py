from __future__ import annotations

import enum
import uuid
from decimal import Decimal

from datetime import date

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from sqlalchemy import Numeric

from app.database.base import Base, Money, Timestamps, UUIDPrimaryKey


class YieldType(str, enum.Enum):
    """Como a conta remunera o saldo."""

    none = "none"
    # Percentual do CDI, a convencao das contas digitais brasileiras.
    cdi_percent = "cdi_percent"


class AccountType(str, enum.Enum):
    checking = "checking"
    savings = "savings"
    investment = "investment"
    cash = "cash"


class Account(Base, UUIDPrimaryKey, Timestamps):
    __tablename__ = "account"
    __table_args__ = (
        CheckConstraint("yield_rate >= 0", name="yield_rate_non_negative"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("app_user.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    bank: Mapped[str | None] = mapped_column(String(80))
    type: Mapped[AccountType] = mapped_column(
        SAEnum(AccountType, name="account_type", native_enum=False, length=16),
        default=AccountType.checking,
        nullable=False,
    )
    # O saldo atual nao e armazenado: e derivado deste valor mais o efeito das
    # transacoes, para nao existir um numero denormalizado que pode divergir.
    initial_balance: Mapped[Decimal] = mapped_column(Money, default=Decimal("0"), nullable=False)
    color: Mapped[str] = mapped_column(String(9), default="#5E7CE2", nullable=False)
    icon: Mapped[str] = mapped_column(String(40), default="bank", nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # -- Rendimento ---------------------------------------------------------
    yield_type: Mapped[YieldType] = mapped_column(
        SAEnum(YieldType, name="yield_type", native_enum=False, length=16),
        default=YieldType.none,
        nullable=False,
    )
    # Percentual do indice: 100 = 100% do CDI, 110 = 110% do CDI.
    yield_rate: Mapped[Decimal] = mapped_column(
        Numeric(7, 4), default=Decimal("0"), nullable=False
    )
    # A partir de quando remunerar. Antes disso o saldo nao rende.
    yield_started_on: Mapped[date | None] = mapped_column(Date)
    # Primeiro dia do ultimo mes ja creditado. Evita recreditar o mesmo mes.
    last_yield_month: Mapped[date | None] = mapped_column(Date)
