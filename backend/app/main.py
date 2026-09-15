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
from app.core.middleware import RateLimitMiddleware, SecurityHeadersMiddleware
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
    docs = settings.show_docs
    app = FastAPI(
        title=settings.app_name,
        description=DESCRIPTION,
        version="1.0.0",
        docs_url="/docs" if docs else None,
        redoc_url="/redoc" if docs else None,
        openapi_url="/openapi.json" if docs else None,
    )

    # A ordem importa: o registrado por ULTIMO e o mais EXTERNO. Queremos, de
    # fora para dentro, CORS -> cabecalhos -> limite. O CORS precisa ser o mais
    # externo: sem os cabecalhos dele na resposta 429, o navegador esconde o
    # corpo e o usuario ve um erro de CORS em vez de "muitas requisicoes".
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        # Cobre os deploy previews do Netlify, cujo subdominio muda a cada build.
        allow_origin_regex=settings.cors_origin_regex or None,
        # A autenticacao e por Bearer token no cabecalho, nao por cookie.
        # Sem credenciais no CORS o navegador nunca anexa cookie de sessao a
        # uma chamada entre origens -- e CSRF deixa de ser possivel por
        # construcao, nao por convencao.
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Accept"],
        max_age=600,
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

    @app.get("/", tags=["Infra"], summary="Raiz da API")
    def root() -> dict[str, str]:
        """Aponta o caminho para quem abre a URL crua no navegador.

        Sem isto a raiz devolve o 404 do roteador, que parece deploy quebrado
        mesmo com a API inteira de pe.
        """
        payload = {
            "name": settings.app_name,
            "health": "/health",
            "api": settings.api_v1_prefix,
        }
        if settings.show_docs:
            payload["docs"] = "/docs"
        return payload

    @app.get("/health", tags=["Infra"], summary="Verificacao de saude")
    def health() -> dict[str, str]:
        return {"status": "ok", "environment": settings.environment}

    return app


app = create_app()
