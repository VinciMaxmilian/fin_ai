from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.categories.models import CategoryKind

HEX_COLOR = r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$"


class CategoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    kind: CategoryKind = CategoryKind.expense
    color: str = Field(default="#8E8E93", pattern=HEX_COLOR)
    icon: str = Field(default="tag", max_length=40)
    parent_id: uuid.UUID | None = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    kind: CategoryKind | None = None
    color: str | None = Field(default=None, pattern=HEX_COLOR)
    icon: str | None = Field(default=None, max_length=40)
    parent_id: uuid.UUID | None = None


class CategoryRead(CategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    is_system: bool
    created_at: datetime
