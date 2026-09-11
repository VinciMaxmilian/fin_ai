"""Blindagem: vincula o perfil ao auth.users e fecha o acesso direto via PostgREST

O Supabase publica o schema `public` como API REST usando a chave anon, que por
definicao e publica (vai no bundle do frontend). Sem esta migration qualquer
pessoa com aquela chave leria e escreveria nas tabelas financeiras direto,
passando por cima de toda a regra de negocio do FastAPI.

Duas travas, porque uma so nao basta:

1. RLS ligada e sem nenhuma policy: o Postgres nega tudo por padrao para quem
   nao tem BYPASSRLS.
2. Privilegios revogados das roles `anon` e `authenticated`: mesmo que alguem
   crie uma policy sem querer no painel, a role continua sem GRANT.

O backend conecta como `postgres`, que tem BYPASSRLS, e segue funcionando
normalmente. Se um dia o app passar a conectar com uma role comum, sera preciso
criar policies explicitas por user_id antes.

Revision ID: 7b2c9d451e88
Revises: 41437c295355
"""
from __future__ import annotations

from typing import Sequence

from alembic import op

revision: str = "7b2c9d451e88"
down_revision: str | None = "41437c295355"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

APP_TABLES = (
    "app_user",
    "account",
    "card",
    "category",
    "transaction",
    "recurring_rule",
    "budget",
    "goal",
    "installment_plan",
    "investment",
)

EXPOSED_ROLES = ("anon", "authenticated")


def upgrade() -> None:
    # Excluir a conta no Supabase Auth deve levar junto os dados financeiros,
    # em vez de deixar um perfil orfao apontando para um usuario inexistente.
    op.execute(
        """
        ALTER TABLE public.app_user
        ADD CONSTRAINT fk_app_user_id_auth_users
        FOREIGN KEY (id) REFERENCES auth.users(id) ON DELETE CASCADE
        """
    )

    for table in APP_TABLES:
        op.execute(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE public.{table} FORCE ROW LEVEL SECURITY")
        for role in EXPOSED_ROLES:
            op.execute(f"REVOKE ALL ON public.{table} FROM {role}")

    for role in EXPOSED_ROLES:
        op.execute(f"REVOKE ALL ON SCHEMA public FROM {role}")
        # Tabelas criadas por migrations futuras ja nascem fechadas.
        op.execute(
            f"ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM {role}"
        )


def downgrade() -> None:
    for role in EXPOSED_ROLES:
        op.execute(f"GRANT USAGE ON SCHEMA public TO {role}")
        op.execute(
            f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO {role}"
        )

    for table in APP_TABLES:
        op.execute(f"ALTER TABLE public.{table} NO FORCE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE public.{table} DISABLE ROW LEVEL SECURITY")
        for role in EXPOSED_ROLES:
            op.execute(f"GRANT ALL ON public.{table} TO {role}")

    op.execute("ALTER TABLE public.app_user DROP CONSTRAINT fk_app_user_id_auth_users")
