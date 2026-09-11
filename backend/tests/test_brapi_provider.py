"""BrapiProvider contra respostas simuladas.

A suite inteira roda sem rede: `httpx.MockTransport` responde no lugar da API.
Os payloads abaixo sao recortes das respostas reais da brapi, capturadas em
11/09/2026.
"""
from decimal import Decimal

import httpx
import pytest

from app.investments.providers.base import (
    FeatureNotAvailableError,
    ProviderUnavailableError,
    SymbolNotFoundError,
)
from app.investments.providers.brapi import BrapiProvider

QUOTE_PETR4 = {
    "results": [
        {
            "symbol": "PETR4",
            "shortName": "PETR4",
            "longName": "Petroleo Brasileiro SA Pfd",
            "currency": "BRL",
            "regularMarketPrice": 48.93,
            "regularMarketDayHigh": 48.95,
            "regularMarketDayLow": 48.09,
            "regularMarketChange": -0.19,
            "regularMarketChangePercent": -0.39,
            "regularMarketTime": "2026-09-11T16:00:30.000Z",
            "regularMarketVolume": 12548700,
            "regularMarketPreviousClose": 48.92,
            "regularMarketOpen": 48.5,
            "marketCap": 667532946855,
            "fiftyTwoWeekLow": 29.31,
            "fiftyTwoWeekHigh": 50.69,
            "logourl": "https://icons.brapi.dev/icons/PETR4.svg",
        }
    ]
}


def provider_with(handler) -> BrapiProvider:
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return BrapiProvider(token="token-de-teste", client=client, max_retries=0)


def json_handler(payload, status_code=200):
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, json=payload)

    return handler


# -- cotacao ----------------------------------------------------------------


def test_le_a_cotacao_e_converte_para_decimal():
    provider = provider_with(json_handler(QUOTE_PETR4))
    quote = provider.get_quote("petr4")

    assert quote.symbol == "PETR4"
    assert quote.price == Decimal("48.93")
    # Decimal, nao float: centavo nao pode escorrer.
    assert isinstance(quote.price, Decimal)
    assert quote.currency == "BRL"
    assert quote.long_name == "Petroleo Brasileiro SA Pfd"
    assert quote.change == Decimal("-0.19")
    assert quote.volume == 12548700
    assert quote.quoted_at is not None


def test_o_token_vai_na_query_e_o_ticker_sobe_para_maiusculas():
    capturado = {}

    def handler(request: httpx.Request) -> httpx.Response:
        capturado["url"] = str(request.url)
        return httpx.Response(200, json=QUOTE_PETR4)

    provider_with(handler).get_quote("petr4")
    assert "/quote/PETR4" in capturado["url"]
    assert "token=token-de-teste" in capturado["url"]


def test_varios_tickers_viram_uma_unica_chamada():
    chamadas = []

    def handler(request: httpx.Request) -> httpx.Response:
        chamadas.append(str(request.url))
        return httpx.Response(
            200,
            json={
                "results": [
                    {"symbol": "PETR4", "regularMarketPrice": 48.93},
                    {"symbol": "VALE3", "regularMarketPrice": 78.0},
                ]
            },
        )

    quotes = provider_with(handler).get_quotes(["PETR4", "VALE3"])
    assert len(chamadas) == 1
    assert set(quotes) == {"PETR4", "VALE3"}
    assert quotes["VALE3"].price == Decimal("78.0")


def test_lista_vazia_nao_chama_a_api():
    chamadas = []

    def handler(request: httpx.Request) -> httpx.Response:
        chamadas.append(request)
        return httpx.Response(200, json={"results": []})

    assert provider_with(handler).get_quotes([]) == {}
    assert chamadas == []


def test_registro_sem_preco_e_descartado():
    payload = {"results": [{"symbol": "XPTO3"}, {"symbol": "PETR4", "regularMarketPrice": 48.93}]}
    quotes = provider_with(json_handler(payload)).get_quotes(["XPTO3", "PETR4"])
    assert set(quotes) == {"PETR4"}


# -- erros -------------------------------------------------------------------


def test_ticker_inexistente():
    payload = {
        "error": True,
        "message": "Nenhum resultado encontrado para os simbolos informados",
        "code": "NOT_FOUND",
    }
    provider = provider_with(json_handler(payload, 404))
    with pytest.raises(SymbolNotFoundError):
        provider.get_quote("NAOEXISTE99")


def test_recurso_bloqueado_pelo_plano():
    payload = {
        "error": True,
        "message": "Criptomoedas requer o plano Startup",
        "code": "FEATURE_NOT_AVAILABLE",
    }
    provider = provider_with(json_handler(payload, 403))
    with pytest.raises(FeatureNotAvailableError):
        provider.get_quote("BTC")


def test_timeout_vira_provedor_indisponivel():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("tempo esgotado", request=request)

    with pytest.raises(ProviderUnavailableError):
        provider_with(handler).get_quote("PETR4")


def test_erro_500_vira_provedor_indisponivel():
    provider = provider_with(json_handler({"results": []}, 500))
    with pytest.raises(ProviderUnavailableError):
        provider.get_quote("PETR4")


def test_resposta_que_nao_e_json():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html>manutencao</html>")

    with pytest.raises(ProviderUnavailableError):
        provider_with(handler).get_quote("PETR4")


def test_repete_apenas_em_erro_transitorio():
    tentativas = []

    def handler(request: httpx.Request) -> httpx.Response:
        tentativas.append(1)
        return httpx.Response(503, json={"results": []})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = BrapiProvider(token="t", client=client, max_retries=2)
    with pytest.raises(ProviderUnavailableError):
        provider.get_quote("PETR4")
    assert len(tentativas) == 3  # a original mais duas repeticoes


def test_nao_repete_em_404():
    tentativas = []

    def handler(request: httpx.Request) -> httpx.Response:
        tentativas.append(1)
        return httpx.Response(404, json={"error": True, "code": "NOT_FOUND", "message": "x"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = BrapiProvider(token="t", client=client, max_retries=2)
    with pytest.raises(SymbolNotFoundError):
        provider.get_quote("NAOEXISTE")
    assert len(tentativas) == 1


# -- historico e dividendos ---------------------------------------------------


def test_historico_converte_epoch_para_data_e_ordena():
    payload = {
        "results": [
            {
                "symbol": "PETR4",
                "regularMarketPrice": 48.93,
                "historicalDataPrice": [
                    {"date": 1786590000, "open": 42.0, "high": 42.5, "low": 41.8,
                     "close": 42.2, "volume": 100, "adjustedClose": 41.9},
                    {"date": 1786503600, "open": 41.5, "high": 41.97, "low": 41.15,
                     "close": 41.45, "volume": 63890300, "adjustedClose": 40.3321},
                ],
            }
        ]
    }
    pontos = provider_with(json_handler(payload)).get_history("PETR4", range_="5d")
    assert len(pontos) == 2
    assert pontos[0].date < pontos[1].date  # ordem cronologica
    assert pontos[0].close == Decimal("41.45")
    assert pontos[0].adjusted_close == Decimal("40.3321")


def test_historico_ausente_devolve_lista_vazia():
    pontos = provider_with(json_handler(QUOTE_PETR4)).get_history("PETR4")
    assert pontos == []


def test_dividendos_ordenados_do_mais_recente_para_o_mais_antigo():
    payload = {
        "results": [
            {
                "symbol": "PETR4",
                "regularMarketPrice": 48.93,
                "dividendsData": {
                    "cashDividends": [
                        {"paymentDate": "2026-01-10T03:00:00.000Z", "rate": 0.5,
                         "label": "DIVIDENDO"},
                        {"paymentDate": "2026-12-21T03:00:00.000Z", "rate": 0.471567,
                         "label": "DIVIDENDO"},
                    ]
                },
            }
        ]
    }
    dividendos = provider_with(json_handler(payload)).get_dividends("PETR4")
    assert len(dividendos) == 2
    assert dividendos[0].payment_date.year == 2026
    assert dividendos[0].payment_date.month == 12
    assert dividendos[0].rate == Decimal("0.471567")


def test_dividendo_sem_valor_e_ignorado():
    payload = {
        "results": [
            {
                "symbol": "PETR4",
                "regularMarketPrice": 1,
                "dividendsData": {"cashDividends": [{"paymentDate": None, "rate": None}]},
            }
        ]
    }
    assert provider_with(json_handler(payload)).get_dividends("PETR4") == []


# -- busca --------------------------------------------------------------------


def test_busca_de_tickers():
    payload = {"stocks": ["PETR4", "PETR3"], "indexes": ["IBOV"]}
    resultados = provider_with(json_handler(payload)).search("petr")
    simbolos = {item.symbol for item in resultados}
    assert simbolos == {"PETR4", "PETR3", "IBOV"}
    assert {item.kind for item in resultados} == {"stock", "index"}


def test_busca_vazia_nao_chama_a_api():
    chamadas = []

    def handler(request: httpx.Request) -> httpx.Response:
        chamadas.append(request)
        return httpx.Response(200, json={})

    assert provider_with(handler).search("   ") == []
    assert chamadas == []
