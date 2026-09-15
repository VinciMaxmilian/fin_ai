"""Ponto de entrada da API."""
from __future__ import annotations

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.accounts.router import router as accounts_router
from app.auth.router import router as auth_router
from app.budgets.router import router as budgets_router
from app.cards.router import router as cards_router
from app.categories.router import router as categories_router
from app.core.config import settings
from app.core.errors import register_error_handlers
from app.goals.router import router as goals_router
from app.installments.router import router as installments_router
from app.investments.router import router as investments_router
from app.recurring.router import router as recurring_router
from app.reports.router import router as reports_router
from app.transactions.router import router as transactions_router
from app.users.router import router as users_router

DESCRIPTION = """
API de gestao financeira pessoal.

A identidade e responsabilidade do **Supabase Auth**: o cliente faz login la e
envia o JWT resultante no cabecalho `Authorization: Bearer <token>`. Esta API
valida o token e e a unica dona das regras de negocio, para que web, iOS e
Android compartilhem exatamente o mesmo comportamento.
"""


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        description=DESCRIPTION,
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        # Cobre os deploy previews do Netlify, cujo subdominio muda a cada build.
        allow_origin_regex=settings.cors_origin_regex or None,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_error_handlers(app)

    api = APIRouter(prefix=settings.api_v1_prefix)
    for router in (
        auth_router,
        users_router,
        accounts_router,
        cards_router,
        categories_router,
        transactions_router,
        recurring_router,
        budgets_router,
        goals_router,
        installments_router,
        investments_router,
        reports_router,
    ):
        api.include_router(router)
    app.include_router(api)

    @app.get("/health", tags=["Infra"], summary="Verificacao de saude")
    def health() -> dict[str, str]:
        return {"status": "ok", "environment": settings.environment}

    return app


app = create_app()
