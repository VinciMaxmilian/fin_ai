"""Provedores de dados de mercado.

Para acrescentar um provedor: implemente `MarketDataProvider` em um arquivo
novo aqui, registre-o em `PROVIDERS` e aponte `MARKET_DATA_PROVIDER` no `.env`
para a chave escolhida. Nenhum servico da carteira precisa mudar.
"""
from __future__ import annotations

from functools import lru_cache

from app.core.config import settings
from app.investments.providers.base import MarketDataProvider
from app.investments.providers.brapi import BrapiProvider

PROVIDERS: dict[str, type[MarketDataProvider]] = {
    "brapi": BrapiProvider,
    # "hgfinance": HgFinanceProvider,
    # "twelvedata": TwelveDataProvider,
}


@lru_cache
def get_market_data_provider() -> MarketDataProvider | None:
    """Provedor configurado, ou None quando a busca automatica esta desligada.

    `None` nao e erro: a carteira funciona inteira sem provedor nenhum, com o
    usuario informando o preco atual na mao.
    """
    key = (settings.market_data_provider or "none").strip().lower()
    provider_class = PROVIDERS.get(key)
    return provider_class() if provider_class else None


__all__ = ["PROVIDERS", "get_market_data_provider", "MarketDataProvider"]
