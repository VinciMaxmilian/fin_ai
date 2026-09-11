"""Importa todos os modelos para que o Alembic enxergue o metadata completo.

Cada modulo de dominio declara seus proprios modelos; este arquivo e o unico
ponto que precisa conhecer todos eles.
"""
from app.accounts.models import Account  # noqa: F401
from app.budgets.models import Budget  # noqa: F401
from app.cards.models import Card  # noqa: F401
from app.categories.models import Category  # noqa: F401
from app.database.base import Base  # noqa: F401
from app.goals.models import Goal  # noqa: F401
from app.installments.models import InstallmentPlan  # noqa: F401
from app.investments.models import Investment  # noqa: F401
from app.recurring.models import RecurringRule  # noqa: F401
from app.transactions.models import Transaction  # noqa: F401
from app.users.models import User  # noqa: F401

__all__ = ["Base"]
