from __future__ import annotations

import enum
import uuid

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, Timestamps, UUIDPrimaryKey


class CategoryKind(str, enum.Enum):
    """Em que tipo de lancamento a categoria pode ser usada."""

    expense = "expense"
    income = "income"
    both = "both"


class Category(Base, UUIDPrimaryKey, Timestamps):
    __tablename__ = "category"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_category_user_id_name"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("app_user.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    kind: Mapped[CategoryKind] = mapped_column(
        SAEnum(CategoryKind, name="category_kind", native_enum=False, length=16),
        default=CategoryKind.expense,
        nullable=False,
    )
    color: Mapped[str] = mapped_column(String(9), default="#8E8E93", nullable=False)
    icon: Mapped[str] = mapped_column(String(40), default="tag", nullable=False)
    # Criada pelo seed inicial. Pode ser renomeada, mas nao excluida.
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("category.id", ondelete="SET NULL")
    )
