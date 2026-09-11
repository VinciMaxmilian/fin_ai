from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str | None
    avatar_url: str | None
    currency: str
    locale: str
    created_at: datetime


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=160)
    avatar_url: str | None = Field(default=None, max_length=1024)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    locale: str | None = Field(default=None, max_length=10)
