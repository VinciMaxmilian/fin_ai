"""Adaptador da API para a Vercel.

A Vercel trata cada arquivo em `api/` como uma serverless function e, quando o
modulo expoe uma variavel chamada `app` que fala ASGI, ela e servida
diretamente -- nao ha handler para escrever. O `vercel.json` reescreve todas as
rotas para ca, entao esta unica function responde pela API inteira.

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

from app.main import app  # noqa: E402

__all__ = ["app"]
