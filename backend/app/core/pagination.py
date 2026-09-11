"""Paginacao por offset, compartilhada por todos os modulos."""
from __future__ import annotations

from typing import Generic, Sequence, TypeVar

from fastapi import Query
from pydantic import BaseModel
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

T = TypeVar("T")


class PageParams(BaseModel):
    page: int = 1
    page_size: int = 50

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


def page_params(
    page: int = Query(1, ge=1, description="Pagina, iniciando em 1"),
    page_size: int = Query(50, ge=1, le=200, description="Itens por pagina"),
) -> PageParams:
    return PageParams(page=page, page_size=page_size)


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int

    @classmethod
    def build(cls, items: Sequence[T], total: int, params: PageParams) -> "Page[T]":
        pages = (total + params.page_size - 1) // params.page_size if params.page_size else 0
        return cls(
            items=list(items),
            total=total,
            page=params.page,
            page_size=params.page_size,
            pages=pages,
        )


def paginate(db: Session, stmt: Select, params: PageParams) -> tuple[Sequence, int]:
    """Executa `stmt` paginada e devolve (linhas, total sem paginacao)."""
    count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
    total = db.execute(count_stmt).scalar_one()
    rows = db.execute(stmt.limit(params.page_size).offset(params.offset)).scalars().all()
    return rows, total
