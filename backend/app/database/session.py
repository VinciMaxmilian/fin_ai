"""Engine, sessao e dependencia de banco de dados."""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings

# O pooler do Supabase nao suporta prepared statements nomeados em modo
# transaction; `prepare_threshold` do psycopg2 nao existe, entao mantemos o
# pool do SQLAlchemy modesto e reciclamos conexoes antes do timeout do pooler.
#
# Em serverless a conta e outra: o processo pode ser congelado logo depois da
# resposta, entao uma conexao guardada no pool fica pendurada no banco sem
# ninguem para devolve-la. NullPool abre e fecha por request e deixa o reuso
# com o pooler do Supabase.
_pool_options: dict[str, object] = (
    {"poolclass": NullPool}
    if settings.db_disable_pool
    else {
        "pool_size": settings.db_pool_size,
        "max_overflow": settings.db_max_overflow,
        "pool_recycle": settings.db_pool_recycle,
    }
)

engine = create_engine(
    settings.sqlalchemy_url,
    pool_pre_ping=settings.db_pool_pre_ping,
    echo=settings.db_echo,
    connect_args={"sslmode": "require", "connect_timeout": 15}
    if "supabase" in settings.sqlalchemy_url
    else {},
    **_pool_options,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """Dependencia FastAPI: abre uma sessao por request e garante o fechamento."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
