"""Testes das defesas transversais: cabecalhos, limite e formato do ticker.

Cobrem regressao de seguranca -- o tipo de detalhe que some em uma refatoracao
sem que nenhum teste funcional perceba.
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.middleware import RateLimitMiddleware, SecurityHeadersMiddleware
from app.investments.tickers import is_valid_ticker, normalize_ticker


@pytest.fixture
def client() -> TestClient:
    """App minima: isola os middlewares das dependencias de banco e rede."""
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/ping")
    def ping() -> dict[str, str]:
        return {"status": "ok"}

    return TestClient(app)


# -- cabecalhos --------------------------------------------------------------


@pytest.mark.parametrize(
    ("header", "expected"),
    [
        ("X-Content-Type-Options", "nosniff"),
        ("X-Frame-Options", "DENY"),
        ("Referrer-Policy", "no-referrer"),
        ("Cache-Control", "no-store"),
    ],
)
def test_resposta_traz_cabecalhos_de_seguranca(
    client: TestClient, header: str, expected: str
) -> None:
    assert client.get("/ping").headers[header] == expected


def test_csp_da_api_proibe_todo_recurso(client: TestClient) -> None:
    csp = client.get("/ping").headers["Content-Security-Policy"]
    assert "default-src 'none'" in csp
    # Sem isto a resposta pode ser embutida em um iframe de outro site.
    assert "frame-ancestors 'none'" in csp


def test_dado_financeiro_nao_pode_ser_cacheado(client: TestClient) -> None:
    """`no-store` evita a resposta ficar no disco ou em um proxy compartilhado."""
    assert "no-store" in client.get("/ping").headers["Cache-Control"]


# -- limite de requisicoes ---------------------------------------------------


def test_excesso_de_requisicoes_recebe_429(client: TestClient, monkeypatch) -> None:
    from app.core import middleware

    monkeypatch.setattr(middleware.settings, "rate_limit_per_minute", 3)

    for _ in range(3):
        assert client.get("/ping").status_code == 200

    blocked = client.get("/ping")
    assert blocked.status_code == 429
    assert blocked.json()["error"]["code"] == "rate_limited"
    assert blocked.headers["Retry-After"] == "60"


def test_429_mantem_os_cabecalhos_de_seguranca(client: TestClient, monkeypatch) -> None:
    """A resposta de bloqueio nao pode ser a brecha que o resto fecha."""
    from app.core import middleware

    monkeypatch.setattr(middleware.settings, "rate_limit_per_minute", 1)
    client.get("/ping")

    blocked = client.get("/ping")
    assert blocked.status_code == 429
    assert blocked.headers["X-Content-Type-Options"] == "nosniff"


def test_health_nao_entra_no_limite(client: TestClient, monkeypatch) -> None:
    """O monitor de uptime bate sem parar e nao pode ser bloqueado."""
    from app.core import middleware

    monkeypatch.setattr(middleware.settings, "rate_limit_per_minute", 1)

    app_health = client.app

    @app_health.get("/health")
    def health() -> dict[str, str]:  # pragma: no cover - registrada no teste
        return {"status": "ok"}

    for _ in range(5):
        assert client.get("/health").status_code == 200


def test_clientes_diferentes_tem_cotas_separadas(client: TestClient, monkeypatch) -> None:
    from app.core import middleware

    monkeypatch.setattr(middleware.settings, "rate_limit_per_minute", 1)

    primeiro = {"X-Forwarded-For": "203.0.113.1"}
    segundo = {"X-Forwarded-For": "203.0.113.2"}

    assert client.get("/ping", headers=primeiro).status_code == 200
    assert client.get("/ping", headers=primeiro).status_code == 429
    # O bloqueio de um cliente nao pode derrubar o outro.
    assert client.get("/ping", headers=segundo).status_code == 200


def test_xff_forjado_nao_escapa_do_limite(client: TestClient, monkeypatch) -> None:
    """O IP confiavel e o ULTIMO da lista: o que o proxy acrescentou.

    Se lessemos o primeiro, bastaria variar o cabecalho a cada chamada para
    ganhar uma cota nova e o limite viraria decoracao.
    """
    from app.core import middleware

    monkeypatch.setattr(middleware.settings, "rate_limit_per_minute", 1)

    assert client.get("/ping", headers={"X-Forwarded-For": "1.1.1.1, 198.51.100.9"}).status_code == 200
    forjado = client.get("/ping", headers={"X-Forwarded-For": "2.2.2.2, 198.51.100.9"})
    assert forjado.status_code == 429


# -- formato do ticker -------------------------------------------------------


@pytest.mark.parametrize("valido", ["PETR4", "bova11", "^BVSP", "BRL=X", "BTC-USD"])
def test_tickers_reais_sao_aceitos(valido: str) -> None:
    assert normalize_ticker(valido) == valido.strip().upper()


@pytest.mark.parametrize(
    "malicioso",
    [
        "../../available",       # troca o caminho na API do provedor
        "PETR4/../../admin",     # idem, escondido apos um ticker valido
        "PETR4?token=roubado",   # injeta parametro na query de saida
        "PETR4#fragmento",       # trunca o restante da URL
        "PETR4 OR 1=1",          # espaco e caractere fora do conjunto
        "A" * 17,                # acima do limite de tamanho
        "",
    ],
)
def test_entrada_que_manipula_a_url_e_recusada(malicioso: str) -> None:
    assert not is_valid_ticker(malicioso)
    with pytest.raises(ValueError):
        normalize_ticker(malicioso)
