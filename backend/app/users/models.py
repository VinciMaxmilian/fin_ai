"""Perfil local do usuario, espelhando a identidade do Supabase Auth."""
from __future__ import annotations

import uuid

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, Timestamps


class User(Base, Timestamps):
    __tablename__ = "app_user"

    # Mesmo UUID de auth.users.id no Supabase. Nao geramos id proprio para nao
    # criar duas identidades para a mesma pessoa.
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    full_name: Mapped[str | None] = mapped_column(String(160))
    avatar_url: Mapped[str | None] = mapped_column(String(1024))
    currency: Mapped[str] = mapped_column(String(3), default="BRL", nullable=False)
    locale: Mapped[str] = mapped_column(String(10), default="pt-BR", nullable=False)

    def __repr__(self) -> str:  # pragma: no cover - auxilio de depuracao
        return f"<User {self.email}>"
