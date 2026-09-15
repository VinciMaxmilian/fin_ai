"""Adaptador da API para a Vercel.

A Vercel trata cada arquivo em `api/` como uma serverless function e, quando o
modulo expoe um objeto ASGI, ela o serve direto -- nao ha handler para escrever.
O `vercel.json` manda todas as rotas para ca, entao esta unica function responde
pela API inteira.

As migrations NAO rodam aqui: uma serverless function pode subir varias
instancias em paralelo e aplicar Alembic em todas seria uma corrida. Rode
`python main.py migrate` apontando para o banco de producao antes do deploy.
"""
from __future__ import annotations

import sys
from pathlib import Path

# A function e executada a partir de api/, mas o pacote `app` vive um nivel
# acima. Sem isso o import abaixo falha em tempo de cold start.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app as fastapi_app  # noqa: E402

# Ponto onde esta function fica montada. Dependendo de como a Vercel resolve a
# rota, o path que chega ao ASGI pode vir prefixado com ele -- e ai nenhuma rota
# do FastAPI casa e tudo vira 404. Removemos o prefixo antes de repassar.
_MOUNT = "/api/index"


async def app(scope, receive, send):  # noqa: ANN001, ANN201
    # So mexe quando ha caminho real depois do prefixo ("/api/index/health" ->
    # "/health"). Um "/api/index" pelado fica como esta: sem sufixo nao da para
    # saber qual era a rota original, e inventar "/" mandaria toda requisicao
    # para o lugar errado.
    if scope["type"] == "http":
        path = scope.get("path", "")
        if path.startswith(_MOUNT + "/"):
            trimmed = path[len(_MOUNT) :]
            scope = dict(scope, path=trimmed, raw_path=trimmed.encode())
    await fastapi_app(scope, receive, send)
