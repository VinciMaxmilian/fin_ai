"""Cache e tolerancia a falha do provedor.

O comportamento que estes testes travam: **a carteira nunca depende da API
externa**. Se o provedor cai, a ultima cotacao conhecida continua valendo,
marcada como desatualizada.
"""
import time
from decimal import Decimal

import pytest

from app.core.cache import InMemoryCache, set_cache
from app.investments.providers.base import (
    AssetSearchResult,
    Dividend,
    HistoricalPoint,
    MarketDataProvider,
    ProviderCapabilities,
    ProviderUnavailableError,
    Quote,
)
from app.investments.services.market_data import MarketDataService


class FakeProvider(MarketDataProvider):
    """Provedor controlado: conta chamadas e pode ser derrubado de proposito."""

    name = "fake"

    def __init__(self, price="48.93"):
        self.calls = 0
        self.fail = False
        self.price = price

    @property
    def capabilities(self):
        return ProviderCapabilities(crypto=False)

    def get_quotes(self, symbols):
        self.calls += 1
        if self.fail:
            raise ProviderUnavailableError("provedor fora do ar")
        return {
            symbol.upper(): Quote(symbol=symbol.upper(), price=Decimal(self.price))
            for symbol in symbols
        }

    def get_history(self, symbol, *, range_="1mo", interval="1d"):
        self.calls += 1
        if self.fail:
            raise ProviderUnavailableError("provedor fora do ar")
        from datetime import date

        return [
            HistoricalPoint(
                date=date(2026, 9, 10),
                open=Decimal("42"),
                high=Decimal("43"),
                low=Decimal("41"),
                close=Decimal("42.5"),
            )
        ]

    def get_dividends(self, symbol):
        self.calls += 1
        if self.fail:
            raise ProviderUnavailableError("provedor fora do ar")
        return [Dividend(payment_date=None, rate=Decimal("0.5"))]

    def search(self, term):
        self.calls += 1
        if self.fail:
            raise ProviderUnavailableError("provedor fora do ar")
        return [AssetSearchResult(symbol="PETR4")]


@pytest.fixture
def service(monkeypatch):
    """MarketDataService com provedor falso e cache limpo."""
    set_cache(InMemoryCache())
    provider = FakeProvider()
    instance = MarketDataService()
    instance._provider = provider
    instance.provider = provider  # atalho para os testes lerem o contador
    return instance


def test_primeira_consulta_vai_ao_provedor(service):
    resultado = service.get_quote("PETR4")
    assert resultado.quote.price == Decimal("48.93")
    assert resultado.is_stale is False
    assert service.provider.calls == 1


def test_segunda_consulta_sai_do_cache(service):
    service.get_quote("PETR4")
    service.get_quote("PETR4")
    service.get_quote("petr4")  # caixa diferente, mesma chave
    assert service.provider.calls == 1


def test_cache_vencido_busca_de_novo(service, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "quote_cache_ttl_seconds", 0)
    service.get_quote("PETR4")
    time.sleep(0.01)
    service.get_quote("PETR4")
    assert service.provider.calls == 2


def test_provedor_fora_do_ar_devolve_a_cotacao_antiga_marcada(service, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "quote_cache_ttl_seconds", 0)
    service.get_quote("PETR4")  # popula o cache
    time.sleep(0.01)

    service.provider.fail = True
    resultado = service.get_quote("PETR4")

    assert resultado is not None
    assert resultado.quote.price == Decimal("48.93")
    assert resultado.is_stale is True  # a interface precisa avisar


def test_provedor_fora_do_ar_sem_cache_nao_levanta_excecao(service):
    service.provider.fail = True
    assert service.get_quote("PETR4") is None
    assert service.get_quotes(["PETR4", "VALE3"]) == {}


def test_cotacao_antiga_demais_nao_e_reaproveitada(service, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "quote_cache_ttl_seconds", 0)
    monkeypatch.setattr(settings, "quote_stale_max_age_seconds", 0)
    service.get_quote("PETR4")
    time.sleep(0.01)

    service.provider.fail = True
    assert service.get_quote("PETR4") is None


def test_lote_busca_no_provedor_apenas_o_que_falta(service):
    service.get_quote("PETR4")
    assert service.provider.calls == 1

    resultado = service.get_quotes(["PETR4", "VALE3"])
    assert set(resultado) == {"PETR4", "VALE3"}
    assert service.provider.calls == 2


def test_invalidar_forca_nova_consulta(service):
    service.get_quote("PETR4")
    service.invalidate_quotes(["PETR4"])
    service.get_quote("PETR4")
    assert service.provider.calls == 2


def test_historico_e_cacheado(service):
    service.get_history("PETR4")
    service.get_history("PETR4")
    assert service.provider.calls == 1


def test_historico_fora_do_ar_sem_cache_devolve_vazio(service):
    service.provider.fail = True
    assert service.get_history("PETR4") == []


def test_dividendos_sao_cacheados(service):
    service.get_dividends("PETR4")
    service.get_dividends("PETR4")
    assert service.provider.calls == 1


def test_busca_e_cacheada(service):
    service.search("petr")
    service.search("PETR")
    assert service.provider.calls == 1


def test_sem_provedor_tudo_responde_vazio():
    set_cache(InMemoryCache())
    service = MarketDataService()
    service._provider = None

    assert service.is_enabled is False
    assert service.get_quotes(["PETR4"]) == {}
    assert service.get_history("PETR4") == []
    assert service.get_dividends("PETR4") == []
    assert service.search("petr") == []


# -- o cache em si -----------------------------------------------------------


def test_cache_devolve_entrada_vencida_para_quem_pedir():
    cache = InMemoryCache()
    cache.set("k", "v", ttl_seconds=0)
    time.sleep(0.01)

    entrada = cache.get("k")
    assert entrada is not None
    assert entrada.is_fresh is False
    assert entrada.value == "v"
    # get_fresh ignora o que venceu.
    assert cache.get_fresh("k") is None


def test_cache_respeita_o_limite_de_entradas():
    cache = InMemoryCache(max_entries=10)
    for index in range(40):
        cache.set(f"k{index}", index, ttl_seconds=60)
    assert len(cache._data) <= 10
