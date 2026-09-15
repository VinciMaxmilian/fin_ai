# --- build ------------------------------------------------------------------
# O compilador e os headers de desenvolvimento so servem para montar as wheels.
# Deixa-los na imagem final daria a um invasor as ferramentas para compilar o
# que quisesse dentro do container, entao o build fica em um estagio separado.
FROM python:3.12-slim AS build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip wheel --wheel-dir /wheels -r requirements.txt

# --- runtime ----------------------------------------------------------------
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# libpq5 e a biblioteca de runtime do psycopg2; curl atende ao healthcheck.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=build /wheels /wheels
COPY requirements.txt .
RUN pip install --no-index --find-links=/wheels -r requirements.txt \
    && rm -rf /wheels

COPY . .

# Sem isto o processo roda como root: qualquer falha que permita executar
# comandos no container comeca com privilegio total. O usuario nao e dono do
# codigo, entao tambem nao consegue reescrever a propria aplicacao.
RUN useradd --system --create-home --uid 1001 api \
    && chown -R root:root /app \
    && chmod -R a-w /app
USER api

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
