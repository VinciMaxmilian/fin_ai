"""Cache com expiracao, usado para nao repetir chamadas a provedores externos.

A implementacao atual vive na memoria do processo. A interface e deliberadamente
a mesma que um cache Redis teria (`get` / `set` / `delete`), entao trocar por
Redis mais tarde e implementar `CacheBackend` e mudar uma linha em
`get_cache()` -- nada nos servicos precisa saber qual backend esta ativo.

Limitacao conhecida do backend em memoria: cada processo tem o seu proprio
cache. Com varios workers do uvicorn, a mesma cotacao pode ser buscada uma vez
por worker. Aceitavel para dado de mercado; se virar problema, o sinal para
trocar por Redis ja e esse.
"""
from __future__ import annotations

import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CacheEntry:
    value: Any
    stored_at: float
    expires_at: float

    @property
    def age_seconds(self) -> float:
        return time.time() - self.stored_at

    @property
    def is_fresh(self) -> bool:
        return time.time() < self.expires_at


class CacheBackend(ABC):
    @abstractmethod
    def get(self, key: str) -> CacheEntry | None:
        """Devolve a entrada mesmo vencida. Quem chama decide se ainda serve."""

    @abstractmethod
    def set(self, key: str, value: Any, ttl_seconds: int) -> None: ...

    @abstractmethod
    def delete(self, key: str) -> None: ...

    @abstractmethod
    def clear(self) -> None: ...

    def get_fresh(self, key: str) -> Any | None:
        """Atalho para quando o valor vencido nao interessa."""
        entry = self.get(key)
        return entry.value if entry and entry.is_fresh else None


class InMemoryCache(CacheBackend):
    """Dicionario com TTL, protegido por lock.

    O lock existe porque o FastAPI executa os endpoints `def` em um pool de
    threads: sem ele, duas requisicoes simultaneas poderiam corromper o dict.
    """

    def __init__(self, max_entries: int = 2000) -> None:
        self._data: dict[str, CacheEntry] = {}
        self._lock = threading.Lock()
        self._max_entries = max_entries

    def get(self, key: str) -> CacheEntry | None:
        with self._lock:
            return self._data.get(key)

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        now = time.time()
        entry = CacheEntry(value=value, stored_at=now, expires_at=now + ttl_seconds)
        with self._lock:
            if len(self._data) >= self._max_entries:
                self._evict_locked(now)
            self._data[key] = entry

    def delete(self, key: str) -> None:
        with self._lock:
            self._data.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._data.clear()

    def _evict_locked(self, now: float) -> None:
        """Remove o que ja venceu; se nao bastar, descarta as entradas mais antigas."""
        expired = [key for key, entry in self._data.items() if entry.expires_at < now]
        for key in expired:
            del self._data[key]

        if len(self._data) < self._max_entries:
            return

        oldest = sorted(self._data.items(), key=lambda item: item[1].stored_at)
        for key, _ in oldest[: len(self._data) // 4 or 1]:
            del self._data[key]


_cache: CacheBackend = InMemoryCache()


def get_cache() -> CacheBackend:
    """Ponto unico de troca de backend. Para usar Redis, devolva outro aqui."""
    return _cache


def set_cache(backend: CacheBackend) -> None:
    """Substitui o backend. Usado pelos testes para isolar um do outro."""
    global _cache
    _cache = backend
