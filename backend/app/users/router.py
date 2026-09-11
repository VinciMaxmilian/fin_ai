from __future__ import annotations

from fastapi import APIRouter

from app.core.deps import CurrentUser, DbSession
from app.users.schemas import UserRead, UserUpdate
from app.users.service import UserService

router = APIRouter(prefix="/users", tags=["Usuarios"])


@router.get("/me", response_model=UserRead, summary="Perfil do usuario autenticado")
def read_me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)


@router.patch("/me", response_model=UserRead, summary="Atualiza o perfil")
def update_me(payload: UserUpdate, user: CurrentUser, db: DbSession) -> UserRead:
    data = payload.model_dump(exclude_unset=True)
    return UserRead.model_validate(UserService(db).update(user, data))
