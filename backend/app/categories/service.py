from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.categories.models import Category, CategoryKind
from app.core.errors import ConflictError
from app.core.service import OwnedResourceService
from app.transactions.models import Transaction


class CategoryService(OwnedResourceService[Category]):
    model = Category
    label = "Categoria"

    def list_categories(self, kind: CategoryKind | None = None) -> Sequence[Category]:
        stmt = self.scoped()
        if kind is not None and kind is not CategoryKind.both:
            stmt = stmt.where(Category.kind.in_([kind, CategoryKind.both]))
        return self.db.execute(stmt.order_by(Category.name)).scalars().all()

    def create(self, data: dict) -> Category:
        try:
            return super().create(data)
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError("Ja existe uma categoria com esse nome.") from exc

    def update(self, resource_id: uuid.UUID, data: dict) -> Category:
        try:
            return super().update(resource_id, data)
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError("Ja existe uma categoria com esse nome.") from exc

    def delete(self, resource_id: uuid.UUID) -> None:
        category = self.get(resource_id)
        if category.is_system:
            raise ConflictError(
                "Categorias padrao nao podem ser excluidas. Renomeie-a se preferir."
            )
        in_use = self.db.execute(
            select(func.count(Transaction.id)).where(
                Transaction.user_id == self.user_id,
                Transaction.category_id == category.id,
            )
        ).scalar_one()
        if in_use:
            raise ConflictError(
                f"Esta categoria esta em uso por {in_use} transacao(oes). "
                "Recategorize-as antes de excluir."
            )
        self.db.delete(category)
        self.db.commit()
