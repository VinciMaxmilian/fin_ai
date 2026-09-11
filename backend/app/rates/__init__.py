"""Taxas de referencia (CDI, Selic) usadas pelas contas remuneradas.

Para trocar de fonte: implemente `RateProvider`, registre em `PROVIDERS` e
aponte `RATE_PROVIDER` no `.env`.
"""
from app.rates.base import DailyRate, RateProvider, RateUnavailableError
from app.rates.service import RateService, get_rate_provider

__all__ = [
    "DailyRate",
    "RateProvider",
    "RateService",
    "RateUnavailableError",
    "get_rate_provider",
]
