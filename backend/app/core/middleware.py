"""Middlewares transversais de seguranca: cabecalhos e limite de requisicoes.

Sao duas preocupacoes diferentes que compartilham o mesmo ponto de encaixe (o
ciclo request/response), entao vivem juntas aqui em vez de espalhadas pelo
`create_app`.
"""
from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import settings

# A API so devolve JSON. Uma CSP que proibe tudo garante que uma resposta
# servida com content-type errado (ou aberta direto no navegador) nao consiga
# executar script nem carregar recurso externo.
API_CSP = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"

# O Swagger UI e o ReDoc montam a pagina com JS e CSS vindos do CDN da jsdelivr
# e precisam de uma politica propria -- a de cima deixaria a pagina em branco.
DOCS_CSP = (
    "default-src 'self'; "
    "script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
    "style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
    "img-src 'self' https://fastapi.tiangolo.com data:; "
    "font-src 'self' https://cdn.jsdelivr.net; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; base-uri 'none'"
)

DOCS_PATHS = ("/docs", "/redoc", "/openapi.json")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adiciona os cabecalhos de defesa em profundidade a toda resposta."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        headers = response.headers

        # Impede o navegador de "adivinhar" o tipo do conteudo -- a base de
        # varios XSS em respostas que deveriam ser apenas dados.
        headers.setdefault("X-Content-Type-Options", "nosniff")
        # A API nunca precisa ser renderizada dentro de um frame.
        headers.setdefault("X-Frame-Options", "DENY")
        headers.setdefault("Referrer-Policy", "no-referrer")
        headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
        # Sem isto, respostas com dado financeiro podem ficar guardadas em
        # cache compartilhado (proxy) ou no disco do navegador.
        headers.setdefault("Cache-Control", "no-store")

        is_docs = request.url.path.startswith(DOCS_PATHS)
        headers.setdefault("Content-Security-Policy", DOCS_CSP if is_docs else API_CSP)

        # HSTS so faz sentido sobre HTTPS; em HTTP o navegador ignora e em
        # desenvolvimento (localhost) atrapalha.
        if settings.environment != "development":
            headers.setdefault(
                "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
            )

        return response


class _SlidingWindow:
    """Contador de requisicoes por chave em uma janela deslizante.

    Vive na memoria do processo, igual ao cache de cotacoes. Em serverless cada
    instancia tem o proprio contador, entao o limite efetivo e por instancia --
    ainda assim corta o abuso vindo de um unico cliente, que e o caso comum.
    Se um dia precisar ser exato entre instancias, o lugar de trocar por Redis
    e esta classe.
    """

    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()
        self._last_sweep = time.monotonic()

    def allow(self, key: str, *, limit: int, window: float) -> bool:
        now = time.monotonic()
        with self._lock:
            self._sweep(now, window)
            hits = self._hits[key]
            while hits and now - hits[0] >= window:
                hits.popleft()
            if len(hits) >= limit:
                return False
            hits.append(now)
            return True

    def _sweep(self, now: float, window: float) -> None:
        """Descarta chaves ociosas para o dicionario nao crescer sem limite."""
        if now - self._last_sweep < window:
            return
        self._last_sweep = now
        vazias = [
            key
            for key, hits in self._hits.items()
            if not hits or now - hits[-1] >= window
        ]
        for key in vazias:
            del self._hits[key]


def client_key(request: Request) -> str:
    """Identifica o chamador para fins de limite.

    Atras de um proxy (Vercel, Netlify, nginx) o IP do socket e sempre o do
    proxy; o IP real vem em `X-Forwarded-For`. O cliente pode forjar esse
    cabecalho, mas o proxy acrescenta o IP observado no fim da lista, entao o
    ULTIMO valor e o unico em que da para confiar.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        parts = [part.strip() for part in forwarded.split(",") if part.strip()]
        if parts:
            return parts[-1]
    client = request.client
    return client.host if client else "desconhecido"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Teto de requisicoes por cliente, com um teto menor no que custa caro.

    Os endpoints de mercado saem para a brapi, que tem cota. Sem limite, um
    unico cliente em loop queima a cota do projeto inteiro -- e nao e preciso
    ma-fe para isso, um `useEffect` mal escrito basta.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self._window = _SlidingWindow()

    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS" or request.url.path == "/health":
            return await call_next(request)

        key = client_key(request)
        path = request.url.path

        if "/investments/market/" in path:
            bucket, limit = f"market:{key}", settings.rate_limit_market_per_minute
        else:
            bucket, limit = f"geral:{key}", settings.rate_limit_per_minute

        if not self._window.allow(bucket, limit=limit, window=60.0):
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "rate_limited",
                        "message": "Muitas requisicoes. Aguarde um instante e tente de novo.",
                        "details": {},
                    }
                },
                headers={"Retry-After": "60"},
            )

        return await call_next(request)
