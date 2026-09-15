"""Endpoints de apoio a autenticacao.

O login, o cadastro e o refresh acontecem direto no Supabase Auth, a partir do
cliente. O backend so valida o token e expoe a configuracao publica de que o
frontend precisa para se conectar ao provedor.
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings
from app.core.deps import CurrentUser
from app.users.schemas import UserRead

router = APIRouter(prefix="/auth", tags=["Autenticacao"])


class AuthConfig(BaseModel):
    supabase_url: str
    # Chave publicavel (anon). Feita para ficar exposta no cliente.
    supabase_anon_key: str
    providers: list[str]


@router.get("/config", response_model=AuthConfig, summary="Configuracao publica do login")
def auth_config() -> AuthConfig:
    return AuthConfig(
        supabase_url=settings.supabase_url,
        supabase_anon_key=settings.supabase_anon_key,
        # A interface hoje oferece apenas e-mail e senha. O metodo do
        # Google segue implementado em stores/auth.tsx caso volte a ser
        # exposto -- ao reativar, acrescente "google" aqui tambem.
        providers=["password"],
    )


@router.get(
    "/session",
    response_model=UserRead,
    summary="Valida o token e provisiona o perfil local",
)
def current_session(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)
