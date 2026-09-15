from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.categories.defaults import DEFAULT_CATEGORIES
from app.categories.models import Category
from app.core.errors import AuthError
from app.core.security import TokenClaims
from app.users.models import User


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_or_create_from_claims(self, claims: TokenClaims) -> User:
        """Provisiona o perfil local na primeira requisicao autenticada."""
        try:
            user_id = uuid.UUID(claims.subject)
        except ValueError as exc:
            # Token bem assinado, mas com `sub` fora do formato esperado.
            raise AuthError("Token invalido.") from exc
        user = self.db.get(User, user_id)

        if user is not None:
            self._refresh_profile(user, claims)
            return user

        user = User(
            id=user_id,
            email=claims.email or f"{user_id}@sem-email.local",
            full_name=claims.full_name,
            avatar_url=claims.avatar_url,
        )
        self.db.add(user)
        try:
            self.db.flush()
        except IntegrityError:
            # Outra requisicao do mesmo usuario criou o perfil em paralelo.
            self.db.rollback()
            existing = self.db.get(User, user_id)
            if existing is None:  # pragma: no cover - condicao improvavel
                raise
            return existing

        self._seed_categories(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(self, user: User, data: dict) -> User:
        for field, value in data.items():
            setattr(user, field, value)
        self.db.commit()
        self.db.refresh(user)
        return user

    def _refresh_profile(self, user: User, claims: TokenClaims) -> None:
        """Mantem email/nome/avatar em sincronia com o provedor de identidade."""
        changed = False
        if claims.email and claims.email != user.email:
            user.email = claims.email
            changed = True
        if claims.full_name and not user.full_name:
            user.full_name = claims.full_name
            changed = True
        if claims.avatar_url and claims.avatar_url != user.avatar_url:
            user.avatar_url = claims.avatar_url
            changed = True
        if changed:
            self.db.commit()

    def _seed_categories(self, user: User) -> None:
        already = self.db.execute(
            select(Category.id).where(Category.user_id == user.id).limit(1)
        ).first()
        if already:
            return
        self.db.add_all(
            Category(user_id=user.id, is_system=True, **item)  # type: ignore[arg-type]
            for item in DEFAULT_CATEGORIES
        )
