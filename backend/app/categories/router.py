from __future__ import annotations

import uuid

from fastapi import APIRouter, Query, status

from app.categories.models import CategoryKind
from app.categories.schemas import CategoryCreate, CategoryRead, CategoryUpdate
from app.categories.service import CategoryService
from app.core.deps import CurrentUser, DbSession

router = APIRouter(prefix="/categories", tags=["Categorias"])


@router.get("", response_model=list[CategoryRead], summary="Lista as categorias")
def list_categories(
    user: CurrentUser,
    db: DbSession,
    kind: CategoryKind | None = Query(default=None, description="Filtra por tipo de uso"),
) -> list[CategoryRead]:
    rows = CategoryService(db, user.id).list_categories(kind)
    return [CategoryRead.model_validate(row) for row in rows]


@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(payload: CategoryCreate, user: CurrentUser, db: DbSession) -> CategoryRead:
    created = CategoryService(db, user.id).create(payload.model_dump())
    return CategoryRead.model_validate(created)


@router.get("/{category_id}", response_model=CategoryRead)
def read_category(category_id: uuid.UUID, user: CurrentUser, db: DbSession) -> CategoryRead:
    return CategoryRead.model_validate(CategoryService(db, user.id).get(category_id))


@router.patch("/{category_id}", response_model=CategoryRead)
def update_category(
    category_id: uuid.UUID, payload: CategoryUpdate, user: CurrentUser, db: DbSession
) -> CategoryRead:
    data = payload.model_dump(exclude_unset=True)
    return CategoryRead.model_validate(CategoryService(db, user.id).update(category_id, data))


@router.delete("/{category_id}", response_model=None, status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: uuid.UUID, user: CurrentUser, db: DbSession) -> None:
    CategoryService(db, user.id).delete(category_id)
