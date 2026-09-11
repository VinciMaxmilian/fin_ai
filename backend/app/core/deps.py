"""Dependencias compartilhadas: sessao de banco e usuario autenticado."""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.errors import AuthError
from app.core.security import TokenClaims, verify_token
from app.database.session import get_db
from app.users.models import User
from app.users.service import UserService

DbSession = Annotated[Session, Depends(get_db)]

_bearer = HTTPBearer(auto_error=False, description="JWT emitido pelo Supabase Auth")


def get_token_claims(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> TokenClaims:
    if credentials is None or not credentials.credentials:
        raise AuthError("Credenciais ausentes.")
    return verify_token(credentials.credentials)


def get_current_user(
    db: DbSession,
    claims: Annotated[TokenClaims, Depends(get_token_claims)],
) -> User:
    """Usuario da requisicao, criado na primeira vez que o token e apresentado.

    O Supabase e a fonte da verdade da identidade; a tabela local guarda apenas
    o perfil e serve de ancora para as chaves estrangeiras do dominio.
    """
    return UserService(db).get_or_create_from_claims(claims)


CurrentUser = Annotated[User, Depends(get_current_user)]
