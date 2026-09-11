"""Carteira do usuario.

Cruza duas fontes que nao devem ser confundidas:

- **o nosso banco** diz o que o usuario possui (quantidade, preco medio);
- **o provedor de mercado** diz quanto o ativo vale hoje.

A posicao e sempre a fonte da verdade. A cotacao e um enriquecimento: se ela
faltar, a carteira continua inteira, usando o preco que o usuario informou.
"""
from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from typing import Sequence

from sqlalchemy.orm import Session

from app.core.money import ZERO, percentage, quantize
from app.core.service import OwnedResourceService
from app.investments.models import Investment, InvestmentType
from app.investments.services.market_data import MarketDataService, QuoteResult
from app.investments.services.performance import aggregate, compute_position

TYPE_LABELS: dict[str, str] = {
    "stock": "Ações",
    "fii": "FIIs",
    "crypto": "Cripto",
    "fixed_income": "Renda fixa",
    "treasury": "Tesouro",
    "etf": "ETF",
    "other": "Outros",
}

# Classes que a brapi cota por ticker. Renda fixa e tesouro nao tem codigo de
# negociacao; cripto exige plano pago (ver BrapiProvider.capabilities).
QUOTABLE_TYPES = {
    InvestmentType.stock,
    InvestmentType.fii,
    InvestmentType.etf,
    InvestmentType.other,
}


class InvestmentService(OwnedResourceService[Investment]):
    model = Investment
    label = "Investimento"

    def __init__(
        self,
        db: Session,
        user_id: uuid.UUID,
        market_data: MarketDataService | None = None,
    ) -> None:
        super().__init__(db, user_id)
        # Injetavel: os testes passam um dublê e nao tocam a rede.
        self.market_data = market_data or MarketDataService()

    def list_investments(self) -> Sequence[Investment]:
        return self.db.execute(self.scoped().order_by(Investment.asset)).scalars().all()

    # -- cotacoes -----------------------------------------------------------
    def _quotable_tickers(self, investments: Sequence[Investment]) -> list[str]:
        return [
            investment.ticker.upper()
            for investment in investments
            if investment.ticker and investment.type in QUOTABLE_TYPES
        ]

    def _fetch_quotes(self, investments: Sequence[Investment]) -> dict[str, QuoteResult]:
        tickers = self._quotable_tickers(investments)
        if not tickers or not self.market_data.is_enabled:
            return {}
        return self.market_data.get_quotes(tickers)

    def _persist_quotes(
        self, investments: Sequence[Investment], quotes: dict[str, QuoteResult]
    ) -> None:
        """Guarda a ultima cotacao vista, para sobreviver a uma queda da API."""
        changed = False
        now = datetime.now(timezone.utc)

        for investment in investments:
            if not investment.ticker:
                continue
            result = quotes.get(investment.ticker.upper())
            if result is None or result.is_stale:
                continue
            price = quantize(result.quote.price)
            if investment.last_quote_price != price:
                investment.last_quote_price = price
                investment.last_quote_at = now
                changed = True

        if changed:
            self.db.commit()

    def _price_for(
        self, investment: Investment, quotes: dict[str, QuoteResult]
    ) -> tuple[Decimal, str, float | None]:
        """Preco a usar, de onde ele veio e ha quanto tempo.

        A ordem de preferencia e a da confiabilidade: cotacao de agora, cotacao
        guardada, preco informado pelo usuario, preco medio.
        """
        if investment.ticker:
            result = quotes.get(investment.ticker.upper())
            if result is not None:
                source = "stale_quote" if result.is_stale else "quote"
                return quantize(result.quote.price), source, result.age_seconds
            if investment.last_quote_price:
                age = None
                if investment.last_quote_at:
                    age = (datetime.now(timezone.utc) - investment.last_quote_at).total_seconds()
                return quantize(investment.last_quote_price), "stale_quote", age

        if investment.current_price and investment.current_price > 0:
            return quantize(investment.current_price), "manual", None

        return quantize(investment.average_price), "average_price", None

    # -- leitura ------------------------------------------------------------
    def to_read(
        self, investment: Investment, quotes: dict[str, QuoteResult] | None = None
    ) -> dict:
        quotes = quotes if quotes is not None else self._fetch_quotes([investment])
        price, source, age = self._price_for(investment, quotes)
        performance = compute_position(
            quantity=investment.quantity,
            average_price=investment.average_price,
            current_price=price,
        )

        result = quotes.get(investment.ticker.upper()) if investment.ticker else None
        quote = result.quote if result else None

        return {
            "id": investment.id,
            "asset": investment.asset,
            "ticker": investment.ticker,
            "type": investment.type,
            "quantity": investment.quantity,
            "average_price": performance.average_price,
            "current_price": performance.current_price,
            "institution": investment.institution,
            "notes": investment.notes,
            "created_at": investment.created_at,
            "invested_amount": performance.invested_amount,
            "current_value": performance.current_value,
            "profit": performance.profit,
            "profitability": performance.profitability,
            # Procedencia do preco, para a interface poder ser honesta sobre ele.
            "price_source": source,
            "quote_age_seconds": int(age) if age is not None else None,
            "day_change": quantize(quote.change) if quote and quote.change else None,
            "day_change_percent": (
                quantize(quote.change_percent) if quote and quote.change_percent else None
            ),
            "long_name": quote.long_name if quote else None,
            "logo_url": quote.logo_url if quote else None,
        }

    def portfolio(self, *, persist_quotes: bool = True) -> dict:
        """Carteira completa.

        `persist_quotes=False` pula a gravacao da ultima cotacao. O dashboard
        usa isso: ele so precisa do valor total, e uma escrita no meio de um GET
        custava uma ida ao banco por carregamento de pagina. A tela de
        Investimentos continua gravando, que e onde o cache em disco importa.
        """
        investments = self.list_investments()
        quotes = self._fetch_quotes(investments)
        if persist_quotes:
            self._persist_quotes(investments, quotes)

        positions = [self.to_read(investment, quotes) for investment in investments]
        totals = aggregate(
            [
                compute_position(
                    quantity=investment.quantity,
                    average_price=investment.average_price,
                    current_price=self._price_for(investment, quotes)[0],
                )
                for investment in investments
            ]
        )

        by_type: dict[str, Decimal] = defaultdict(lambda: ZERO)
        for position in positions:
            by_type[position["type"].value] += position["current_value"]

        allocation = [
            {
                "type": key,
                "label": TYPE_LABELS.get(key, key),
                "value": quantize(value),
                "percentage": percentage(value, totals.current_value),
            }
            for key, value in sorted(by_type.items(), key=lambda item: item[1], reverse=True)
        ]

        # A interface mostra "atualizado ha X" com base no dado mais antigo.
        ages = [
            position["quote_age_seconds"]
            for position in positions
            if position["quote_age_seconds"] is not None
        ]

        return {
            "invested_amount": totals.invested_amount,
            "current_value": totals.current_value,
            "profit": totals.profit,
            "profitability": totals.profitability,
            "allocation": allocation,
            "positions": positions,
            "market_data": {
                "provider": self.market_data.provider_name,
                "enabled": self.market_data.is_enabled,
                "quoted_positions": len(quotes),
                "oldest_quote_age_seconds": max(ages) if ages else None,
                "has_stale_quotes": any(
                    position["price_source"] == "stale_quote" for position in positions
                ),
                "crypto_supported": bool(
                    self.market_data.capabilities and self.market_data.capabilities.crypto
                ),
            },
        }

    def summary(self) -> dict:
        """So os totais, sem a lista de posicoes. Usado pelo dashboard."""
        portfolio = self.portfolio()
        return {
            key: portfolio[key]
            for key in ("invested_amount", "current_value", "profit", "profitability")
        }

    # -- escrita ------------------------------------------------------------
    def create(self, data: dict) -> Investment:
        return super().create(self._normalize(data))

    def update(self, resource_id: uuid.UUID, data: dict) -> Investment:
        return super().update(resource_id, self._normalize(data))

    @staticmethod
    def _normalize(data: dict) -> dict:
        """Ticker sempre em maiusculas e sem espaco; vazio vira None."""
        if "ticker" in data:
            ticker = (data.get("ticker") or "").strip().upper()
            data = {**data, "ticker": ticker or None}
        return data

    def refresh_quotes(self) -> dict:
        """Forca a releitura das cotacoes, ignorando o cache."""
        self.market_data.invalidate_quotes(self._quotable_tickers(self.list_investments()))
        return self.portfolio()
