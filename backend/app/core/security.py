"""Verificacao dos JWTs emitidos pelo Supabase Auth.

O backend nunca guarda nem valida senhas: a identidade e responsabilidade do
Supabase Auth (GoTrue). Aqui apenas conferimos a assinatura do token, o emissor
e a audiencia, e extraimos as claims que identificam o usuario.

Projetos novos do Supabase assinam com chaves assimetricas (ES256/RS256)
publicadas via JWKS; projetos legados usam um segredo compartilhado HS256.
Os dois caminhos sao suportados.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any

import jwt
from jwt import PyJWKClient

from app.core.config import settings
from app.core.errors import AuthError

ASYMMETRIC_ALGORITHMS = ["ES256", "RS256"]


@dataclass(frozen=True)
class TokenClaims:
    """Subconjunto das claims do Supabase que o app realmente usa."""

    subject: str
    email: str | None
    role: str | None
    session_id: str | None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def full_name(self) -> str | None:
        for key in ("full_name", "name", "user_name"):
            value = self.metadata.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

    @property
    def avatar_url(self) -> str | None:
        for key in ("avatar_url", "picture"):
            value = self.metadata.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None


@lru_cache
def _jwk_client() -> PyJWKClient:
    return PyJWKClient(
        settings.jwks_url,
        cache_keys=True,
        lifespan=settings.jwks_cache_seconds,
    )


def _decode(token: str) -> dict[str, Any]:
    options = {"verify_aud": bool(settings.supabase_jwt_audience)}
    common = {
        "audience": settings.supabase_jwt_audience or None,
        "issuer": settings.jwt_issuer if settings.supabase_url else None,
        "options": options,
    }

    try:
        header = jwt.get_unverified_header(token)
    except jwt.PyJWTError as exc:  # pragma: no cover - token malformado
        raise AuthError("Token invalido.") from exc

    algorithm = header.get("alg")

    if algorithm in ASYMMETRIC_ALGORITHMS:
        if not settings.supabase_url:
            raise AuthError("SUPABASE_URL nao configurada; impossivel validar o token.")
        signing_key = _jwk_client().get_signing_key_from_jwt(token).key
        return jwt.decode(token, signing_key, algorithms=ASYMMETRIC_ALGORITHMS, **common)

    if algorithm == "HS256":
        if not settings.supabase_jwt_secret:
            raise AuthError("Token HS256 recebido, mas SUPABASE_JWT_SECRET nao esta configurado.")
        return jwt.decode(token, settings.supabase_jwt_secret, algorithms=["HS256"], **common)

    raise AuthError(f"Algoritmo de assinatura nao suportado: {algorithm}.")


def verify_token(token: str) -> TokenClaims:
    """Valida o token e devolve as claims. Levanta `AuthError` se invalido."""
    try:
        payload = _decode(token)
    except jwt.ExpiredSignatureError as exc:
        raise AuthError("Sessao expirada. Faca login novamente.") from exc
    except jwt.InvalidAudienceError as exc:
        raise AuthError("Token emitido para outra audiencia.") from exc
    except jwt.InvalidIssuerError as exc:
        raise AuthError("Token emitido por outro provedor.") from exc
    except jwt.PyJWTError as exc:
        raise AuthError("Token invalido.") from exc

    subject = payload.get("sub")
    if not subject:
        raise AuthError("Token sem identificacao de usuario.")

    metadata = payload.get("user_metadata") or {}
    if not isinstance(metadata, dict):
        metadata = {}

    return TokenClaims(
        subject=str(subject),
        email=payload.get("email"),
        role=payload.get("role"),
        session_id=payload.get("session_id"),
        metadata=metadata,
    )
