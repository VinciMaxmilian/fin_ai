"""Ponto de extensao para a camada de IA.

NADA DE IA ESTA IMPLEMENTADO NESTA VERSAO. Este modulo existe para que os
recursos de analise automatica possam ser adicionados sem mexer nos modulos
financeiros: eles definem a fronteira, e so.

Como estender, quando chegar a hora:

1. Escrever uma classe que herde de `AIProvider` (ex.: `GeminiProvider`,
   `OpenAIProvider`, `LocalLLMProvider`) em `app/ai/providers/`.
2. Registra-la em `PROVIDERS`.
3. Apontar `AI_PROVIDER` no `.env` para a chave escolhida.

As ferramentas que a IA vai usar (get_transactions, get_balance, create_
transaction, generate_report, ...) devem ser construidas em cima dos servicos
que ja existem em cada modulo, nunca com SQL proprio: assim a regra de negocio
e a restricao por usuario continuam em um lugar so.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.core.config import settings


class AIProvider(ABC):
    """Contrato minimo que qualquer provedor de IA precisara cumprir."""

    name: str

    @abstractmethod
    def complete(self, prompt: str, **options: Any) -> str:
        """Gera uma resposta em texto."""

    @property
    def is_available(self) -> bool:
        return False


class NullProvider(AIProvider):
    """Provedor ativo hoje: recusa qualquer chamada, de forma explicita."""

    name = "none"

    def complete(self, prompt: str, **options: Any) -> str:
        raise NotImplementedError(
            "Nenhum provedor de IA esta configurado. Defina AI_PROVIDER no .env "
            "depois de implementar um provedor em app/ai/providers/."
        )


PROVIDERS: dict[str, type[AIProvider]] = {"none": NullProvider}


def get_provider() -> AIProvider:
    provider_class = PROVIDERS.get(settings.ai_provider, NullProvider)
    return provider_class()
