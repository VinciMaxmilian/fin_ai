from __future__ import annotations

import enum
import uuid
from decimal import Decimal

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, Money, Quantity, Timestamps, UUIDPrimaryKey


class InvestmentType(str, enum.Enum):
    stock = "stock"
    fii = "fii"
    crypto = "crypto"
    fixed_income = "fixed_income"
    treasury = "treasury"
    etf = "etf"
    other = "other"


class Investment(Base, UUIDPrimaryKey, Timestamps):
    __tablename__ = "investment"
    __table_args__ = (
        CheckConstraint("quantity >= 0", name="quantity_non_negative"),
        CheckConstraint("average_price >= 0", name="average_price_non_negative"),
        CheckConstraint("current_price >= 0", name="current_price_non_negative"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("app_user.id", ondelete="CASCADE"), index=True
    )
    asset: Mapped[str] = mapped_column(String(80), nullable=False)
    # Codigo de negociacao (PETR4, HGLG11, IVVB11...). Quando preenchido, o
    # preco atual e buscado no provedor de dados de mercado; quando vazio, o
    # usuario informa o preco na mao. Renda fixa e tesouro nao tem ticker.
    ticker: Mapped[str | None] = mapped_column(String(16), index=True)
    type: Mapped[InvestmentType] = mapped_column(
        SAEnum(InvestmentType, name="investment_type", native_enum=False, length=20),
        default=InvestmentType.other,
        nullable=False,
    )
    quantity: Mapped[Decimal] = mapped_column(Quantity, default=Decimal("0"), nullable=False)
    average_price: Mapped[Decimal] = mapped_column(Money, default=Decimal("0"), nullable=False)
    # Atualizado manualmente nesta versao; uma cotacao automatica entraria aqui.
    current_price: Mapped[Decimal] = mapped_column(Money, default=Decimal("0"), nullable=False)
    institution: Mapped[str | None] = mapped_column(String(80))
    notes: Mapped[str | None] = mapped_column(String(500))
    # Ultimo preco vindo do provedor, guardado para a carteira continuar
    # legivel se a API externa estiver fora do ar quando o app abrir.
    last_quote_price: Mapped[Decimal | None] = mapped_column(Money)
    last_quote_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
