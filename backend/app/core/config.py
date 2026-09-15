"""Configuracao central da aplicacao, carregada a partir do ambiente."""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, computed_field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Ordem importa: o ULTIMO arquivo vence. A raiz vem primeiro para que
        # backend/.env, que e o especifico, possa sobrescreve-la -- e nao o
        # contrario. Variavel exportada no ambiente do SO ganha dos dois.
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # -- Aplicacao ---------------------------------------------------------
    app_name: str = "La Casa Del Money API"
    api_v1_prefix: str = "/api/v1"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False

    # -- Banco de dados ----------------------------------------------------
    database_url: str = Field(
        default="",
        description="URL SQLAlchemy completa. Tem prioridade sobre as variaveis POSTGRES_*.",
    )
    postgres_user: str = "postgres"
    postgres_password: str = ""
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "postgres"
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_echo: bool = False
    # Testa a conexao antes de cada uso. Custa uma ida ao banco por requisicao
    # -- 186 ms com o banco em Oregon, 11 ms com ele em Sao Paulo. Desligue
    # apenas se aceitar que uma conexao derrubada pelo pooler vire erro em vez
    # de ser reaberta em silencio.
    db_pool_pre_ping: bool = True
    db_pool_recycle: int = 1800
    # Em serverless (Vercel) cada instancia da function teria o proprio pool e
    # as conexoes ficariam abertas depois da resposta, estourando o limite do
    # Supabase. Sem pool, cada request abre e fecha a sua conexao -- o pooler do
    # Supabase (porta 6543) e quem faz o reuso. Liga sozinho na Vercel.
    db_disable_pool: bool = Field(default_factory=lambda: bool(os.getenv("VERCEL")))

    # -- Supabase ----------------------------------------------------------
    supabase_url: str = ""
    supabase_anon_key: str = ""
    # Chave secreta (service_role). Usada apenas para operacoes administrativas
    # no servidor. NUNCA deve chegar ao frontend.
    supabase_service_key: str = ""
    # Audiencia esperada nos JWTs emitidos pelo Supabase Auth.
    supabase_jwt_audience: str = "authenticated"
    # Segredo HS256 legado. Projetos novos usam JWKS assimetrico e deixam vazio.
    supabase_jwt_secret: str = ""
    jwks_cache_seconds: int = 3600

    # -- CORS --------------------------------------------------------------
    # NoDecode: sem ele o pydantic-settings tenta ler o valor do .env como
    # JSON. Queremos aceitar a forma simples "a,b,c".
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]
    # Os deploy previews do Netlify recebem um subdominio novo a cada build, que
    # nao da para listar de antemao. Ex.: https://.*--meu-site\.netlify\.app
    # Vazio (o padrao) mantem so a lista acima.
    cors_origin_regex: str = ""

    # -- Dados de mercado (brapi.dev) --------------------------------------
    market_data_provider: str = "brapi"
    brapi_base_url: str = "https://brapi.dev/api"
    # Segredo: nunca chega ao frontend. Sem ele a brapi ainda responde cotacao,
    # mas com limite de requisicoes bem menor.
    brapi_token: str = ""
    brapi_timeout_seconds: float = 12.0
    brapi_max_retries: int = 2
    # Quantos tickers cabem em uma unica chamada em lote.
    brapi_batch_size: int = 10

    # Por quanto tempo uma cotacao e reaproveitada antes de consultar de novo.
    quote_cache_ttl_seconds: int = 300
    history_cache_ttl_seconds: int = 3600
    dividends_cache_ttl_seconds: int = 21600
    search_cache_ttl_seconds: int = 86400
    # Por quanto tempo uma cotacao vencida ainda pode ser exibida quando o
    # provedor esta fora do ar, marcada como desatualizada.
    quote_stale_max_age_seconds: int = 86400

    # -- Taxas de referencia (Banco Central) -------------------------------
    # Fonte do CDI para as contas remuneradas. "none" desliga o rendimento
    # automatico. A API do BCB e publica e nao exige token.
    rate_provider: str = "bcb"
    bcb_base_url: str = "https://api.bcb.gov.br"
    bcb_timeout_seconds: float = 12.0
    # Serie do mes corrente ainda recebe pontos; a de mes fechado nao muda mais.
    rate_cache_ttl_seconds: int = 21600
    rate_history_cache_ttl_seconds: int = 2592000

    # -- Camada de IA (reservado, nao implementado) ------------------------
    ai_provider: str = "none"
    ai_api_key: str = ""

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sqlalchemy_url(self) -> str:
        """URL efetiva de conexao com o banco."""
        if self.database_url:
            return self.database_url
        from urllib.parse import quote_plus

        password = quote_plus(self.postgres_password)
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def jwks_url(self) -> str:
        return f"{self.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def jwt_issuer(self) -> str:
        return f"{self.supabase_url.rstrip('/')}/auth/v1"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
