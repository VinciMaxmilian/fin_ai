"""Formato aceito para codigos de ativo.

Existe um motivo de seguranca para isto viver separado e ser aplicado nas duas
pontas: o ticker entra pela URL e termina concatenado no caminho de uma chamada
HTTP ao provedor (`/quote/{ticker}`). Sem restricao de caracteres, um valor com
`/`, `?` ou `#` deixa de ser um ticker e vira manipulacao da URL de saida --
outro caminho na API do provedor, ou parametros que nao pedimos.

O conjunto abaixo cobre o que a B3 e a brapi realmente usam (PETR4, BOVA11,
^BVSP, BRL=X, BTC-USD) e nada alem disso.
"""
from __future__ import annotations

import re

TICKER_PATTERN = r"^[A-Za-z0-9.\^=-]{1,16}$"
_TICKER_RE = re.compile(TICKER_PATTERN)


def normalize_ticker(value: str) -> str:
    """Normaliza e valida. Levanta `ValueError` no formato errado."""
    cleaned = value.strip().upper()
    if not _TICKER_RE.match(cleaned):
        raise ValueError(
            "Codigo de ativo invalido. Use apenas letras, numeros e . ^ = - "
            "(ate 16 caracteres)."
        )
    return cleaned


def is_valid_ticker(value: str) -> bool:
    return bool(_TICKER_RE.match(value.strip().upper()))
