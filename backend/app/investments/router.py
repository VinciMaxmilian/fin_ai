from __future__ import annotations

import uuid
from dataclasses import asdict

from fastapi import APIRouter, Path, Query, status

from app.core.deps import CurrentUser, DbSession
from app.core.errors import NotFoundError, ValidationError
from app.investments.providers.base import (
    FeatureNotAvailableError,
    MarketDataError,
    SymbolNotFoundError,
)
from app.investments.schemas import (
    AssetSearchRead,
    DividendRead,
    HistoricalPointRead,
    InvestmentCreate,
    InvestmentRead,
    InvestmentUpdate,
    MarketCapabilitiesRead,
    PortfolioRead,
    PortfolioSummary,
    QuoteRead,
)
from app.investments.services import InvestmentService, MarketDataService
from app.investments.tickers import TICKER_PATTERN

router = APIRouter(prefix="/investments", tags=["Investimentos"])

# Intervalos que a brapi aceita. Restringimos aqui para uma entrada errada
# virar 422 nossa, em vez de uma chamada desperdicada no provedor.
VALID_RANGES = {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"}
VALID_INTERVALS = {"1d", "5d", "1wk", "1mo", "3mo"}


@router.get("", response_model=PortfolioRead, summary="Carteira com cotacoes atuais")
def portfolio(user: CurrentUser, db: DbSession) -> PortfolioRead:
    return PortfolioRead.model_validate(InvestmentService(db, user.id).portfolio())


@router.get(
    "/summary",
    response_model=PortfolioSummary,
    summary="Apenas os totais da carteira",
)
def summary(user: CurrentUser, db: DbSession) -> PortfolioSummary:
    return PortfolioSummary.model_validate(InvestmentService(db, user.id).summary())


@router.post(
    "/refresh",
    response_model=PortfolioRead,
    summary="Descarta o cache e busca as cotacoes de novo",
)
def refresh(user: CurrentUser, db: DbSession) -> PortfolioRead:
    return PortfolioRead.model_validate(InvestmentService(db, user.id).refresh_quotes())


# -- dados de mercado --------------------------------------------------------
# Declarados antes de /{investment_id} para "market" nao ser lido como um UUID.


@router.get(
    "/market/capabilities",
    response_model=MarketCapabilitiesRead,
    summary="O que o provedor entrega no plano atual",
)
def capabilities() -> MarketCapabilitiesRead:
    service = MarketDataService()
    caps = service.capabilities
    return MarketCapabilitiesRead(
        provider=service.provider_name,
        enabled=service.is_enabled,
        quotes=bool(caps and caps.quotes),
        history=bool(caps and caps.history),
        dividends=bool(caps and caps.dividends),
        search=bool(caps and caps.search),
        crypto=bool(caps and caps.crypto),
        notes=caps.unsupported_notes if caps else {},
    )


@router.get(
    "/market/search",
    response_model=list[AssetSearchRead],
    summary="Busca tickers pelo codigo",
)
def search_assets(
    _: CurrentUser,
    term: str = Query(
        min_length=1,
        max_length=16,
        pattern=TICKER_PATTERN,
        description="Trecho do codigo",
    ),
) -> list[AssetSearchRead]:
    results = MarketDataService().search(term)
    return [AssetSearchRead(symbol=item.symbol, kind=item.kind) for item in results]


@router.get(
    "/market/{ticker}/quote",
    response_model=QuoteRead,
    summary="Cotacao atual de um ticker",
)
def quote(
    _: CurrentUser,
    ticker: str = Path(pattern=TICKER_PATTERN, description="Codigo do ativo"),
) -> QuoteRead:
    result = MarketDataService().get_quote(ticker)
    if result is None:
        raise NotFoundError(
            f"Nao foi possivel obter a cotacao de {ticker.upper()}. "
            "Verifique o codigo ou tente novamente em instantes."
        )
    return QuoteRead(
        **asdict(result.quote),
        age_seconds=int(result.age_seconds),
        is_stale=result.is_stale,
    )


@router.get(
    "/market/{ticker}/history",
    response_model=list[HistoricalPointRead],
    summary="Historico de precos",
)
def history(
    _: CurrentUser,
    ticker: str = Path(pattern=TICKER_PATTERN, description="Codigo do ativo"),
    range: str = Query(default="1mo", description="1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max"),
    interval: str = Query(default="1d", description="1d, 5d, 1wk, 1mo, 3mo"),
) -> list[HistoricalPointRead]:
    if range not in VALID_RANGES:
        raise ValidationError(f"Periodo invalido. Use um de: {', '.join(sorted(VALID_RANGES))}.")
    if interval not in VALID_INTERVALS:
        raise ValidationError(
            f"Intervalo invalido. Use um de: {', '.join(sorted(VALID_INTERVALS))}."
        )

    try:
        points = MarketDataService().get_history(ticker, range_=range, interval=interval)
    except SymbolNotFoundError as exc:
        raise NotFoundError(str(exc)) from exc
    except FeatureNotAvailableError as exc:
        raise ValidationError(str(exc)) from exc
    except MarketDataError as exc:
        raise NotFoundError(
            "Dados de mercado indisponiveis no momento. Tente novamente em instantes."
        ) from exc

    return [HistoricalPointRead(**asdict(point)) for point in points]


@router.get(
    "/market/{ticker}/dividends",
    response_model=list[DividendRead],
    summary="Dividendos pagos",
)
def dividends(
    _: CurrentUser,
    ticker: str = Path(pattern=TICKER_PATTERN, description="Codigo do ativo"),
    limit: int = Query(default=24, ge=1, le=200),
) -> list[DividendRead]:
    try:
        rows = MarketDataService().get_dividends(ticker)
    except SymbolNotFoundError as exc:
        raise NotFoundError(str(exc)) from exc
    except FeatureNotAvailableError as exc:
        raise ValidationError(str(exc)) from exc
    except MarketDataError as exc:
        raise NotFoundError(
            "Dados de mercado indisponiveis no momento. Tente novamente em instantes."
        ) from exc

    return [DividendRead(**asdict(item)) for item in rows[:limit]]


# -- carteira ----------------------------------------------------------------


@router.post("", response_model=InvestmentRead, status_code=status.HTTP_201_CREATED)
def create_investment(
    payload: InvestmentCreate, user: CurrentUser, db: DbSession
) -> InvestmentRead:
    service = InvestmentService(db, user.id)
    created = service.create(payload.model_dump())
    return InvestmentRead.model_validate(service.to_read(created))


@router.get("/{investment_id}", response_model=InvestmentRead)
def read_investment(
    investment_id: uuid.UUID, user: CurrentUser, db: DbSession
) -> InvestmentRead:
    service = InvestmentService(db, user.id)
    return InvestmentRead.model_validate(service.to_read(service.get(investment_id)))


@router.patch("/{investment_id}", response_model=InvestmentRead)
def update_investment(
    investment_id: uuid.UUID,
    payload: InvestmentUpdate,
    user: CurrentUser,
    db: DbSession,
) -> InvestmentRead:
    service = InvestmentService(db, user.id)
    updated = service.update(investment_id, payload.model_dump(exclude_unset=True))
    return InvestmentRead.model_validate(service.to_read(updated))


@router.delete(
    "/{investment_id}",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_investment(investment_id: uuid.UUID, user: CurrentUser, db: DbSession) -> None:
    InvestmentService(db, user.id).delete(investment_id)
