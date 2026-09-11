"""Base para servicos de recursos que pertencem a um usuario.

Toda leitura e escrita passa por aqui filtrando por `user_id`, o que torna
impossivel devolver dado de um usuario para outro por esquecimento em um
endpoint novo.
"""
from __future__ import annotations

import uuid
from typing import Any, Generic, Sequence, TypeVar

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError

ModelT = TypeVar("ModelT")


class OwnedResourceService(Generic[ModelT]):
    model: type[ModelT]
    # Nome usado nas mensagens de erro.
    label: str = "Registro"

    def __init__(self, db: Session, user_id: uuid.UUID) -> None:
        self.db = db
        self.user_id = user_id

    # -- consultas ---------------------------------------------------------
    def scoped(self) -> Select:
        """SELECT ja restrito ao usuario corrente."""
        return select(self.model).where(self.model.user_id == self.user_id)  # type: ignore[attr-defined]

    def get(self, resource_id: uuid.UUID) -> ModelT:
        obj = self.db.execute(
            self.scoped().where(self.model.id == resource_id)  # type: ignore[attr-defined]
        ).scalar_one_or_none()
        if obj is None:
            raise NotFoundError(f"{self.label} nao encontrado.")
        return obj

    def get_optional(self, resource_id: uuid.UUID | None) -> ModelT | None:
        if resource_id is None:
            return None
        return self.get(resource_id)

    def list_all(self) -> Sequence[ModelT]:
        return self.db.execute(self.scoped()).scalars().all()

    # -- escrita -----------------------------------------------------------
    def create(self, data: dict[str, Any]) -> ModelT:
        obj = self.model(user_id=self.user_id, **data)  # type: ignore[call-arg]
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(self, resource_id: uuid.UUID, data: dict[str, Any]) -> ModelT:
        obj = self.get(resource_id)
        for field, value in data.items():
            setattr(obj, field, value)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, resource_id: uuid.UUID) -> None:
        obj = self.get(resource_id)
        self.db.delete(obj)
        self.db.commit()
