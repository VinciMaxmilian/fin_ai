# Integração de dados de mercado — brapi.dev

Relatório da implementação. Data: **11/09/2026**.

---

## Resultado

| Verificação | Resultado |
|---|---|
| Testes unitários do backend | **69 passando** (eram 26) |
| Teste ponta a ponta da integração | **27 verificações, 0 falhas** |
| Lint (ruff F,E9) | limpo |
| Typecheck do frontend | limpo |
| Build do frontend | ok |
| Rotas novas | 6 |

Validado contra a API real: PETR4 cotada ao vivo, histórico de 6 meses,
175 registros de dividendos, busca de tickers e a carteira consolidada no
dashboard.

---

## Arquitetura

```
React  ──>  FastAPI  ──>  InvestmentService  ──>  MarketDataService
                                                        │
                                                   cache (TTL)
                                                        │
                                                 MarketDataProvider
                                                        │
                                                   BrapiProvider  ──>  brapi.dev
```

O navegador **nunca** fala com a brapi. O token é segredo de servidor: não
aparece em JavaScript, HTML, respostas da API, logs nem mensagens de erro.

Duas fontes que o código mantém separadas de propósito:

- **nosso banco** diz o que o usuário possui (quantidade, preço médio);
- **o provedor** diz quanto o ativo vale hoje.

A posição é sempre a fonte da verdade. A cotação é enriquecimento.

---

## Arquivos criados

### Backend

| Arquivo | O que faz |
|---|---|
| `app/core/cache.py` | Cache com TTL. Interface igual à do Redis, para a troca ser de uma linha |
| `app/investments/providers/__init__.py` | Registro de provedores e seleção por `.env` |
| `app/investments/providers/base.py` | `MarketDataProvider`, DTOs (`Quote`, `HistoricalPoint`, `Dividend`) e exceções |
| `app/investments/providers/brapi.py` | **Único arquivo que fala HTTP com a brapi** |
| `app/investments/services/__init__.py` | Exporta os serviços do módulo |
| `app/investments/services/market_data.py` | Cache, retry e degradação quando o provedor cai |
| `app/investments/services/performance.py` | Aritmética da carteira. Funções puras, sem banco e sem rede |
| `app/investments/services/portfolio.py` | Cruza posição × cotação. Substitui o antigo `service.py` |
| `tests/test_performance.py` | 10 testes de cálculo |
| `tests/test_brapi_provider.py` | 18 testes do provider, todos com `httpx.MockTransport` |
| `tests/test_market_data.py` | 15 testes de cache e tolerância a falha |
| `alembic/versions/20260911_1305_ticker_e_ultima_cotacao_no_investimento.py` | Migration |

### Frontend

| Arquivo | O que faz |
|---|---|
| `src/components/investments/TickerField.tsx` | Campo de código com sugestões e cotação ao vivo |
| `src/components/investments/AssetDetail.tsx` | Histórico de preço e dividendos do ativo |
| `src/components/investments/ticker-field.css` | Estilos do campo e dos avisos de procedência |

## Arquivos modificados

**Backend**: `app/core/config.py` (variáveis novas), `app/investments/models.py`
(colunas novas), `app/investments/schemas.py`, `app/investments/router.py`,
`app/reports/service.py` (import).
**Removido**: `app/investments/service.py`, que virou o pacote `services/`.

**Frontend**: `src/types/api.ts`, `src/services/endpoints.ts`,
`src/pages/InvestmentsPage.tsx`, `src/utils/format.ts` (`formatQuantity`).

**Raiz**: `.env`, `.env.example`.

---

## Endpoints novos

| Método | Rota | O que faz |
|---|---|---|
| `GET` | `/api/v1/investments/summary` | Só os totais da carteira |
| `POST` | `/api/v1/investments/refresh` | Descarta o cache e busca as cotações de novo |
| `GET` | `/api/v1/investments/market/capabilities` | O que o provedor entrega no plano atual |
| `GET` | `/api/v1/investments/market/search?term=` | Busca tickers pelo código |
| `GET` | `/api/v1/investments/market/{ticker}/quote` | Cotação atual |
| `GET` | `/api/v1/investments/market/{ticker}/history` | Histórico de preços |
| `GET` | `/api/v1/investments/market/{ticker}/dividends` | Dividendos pagos |

`GET /api/v1/investments` (carteira) agora devolve, além das posições, o bloco
`market_data` com a procedência dos preços.

---

## Migration

`20260911_1305_ticker_e_ultima_cotacao_no_investimento` adiciona à tabela
`investment`:

| Coluna | Para quê |
|---|---|
| `ticker` (varchar 16, indexado) | Código de negociação. Preenchido, a cotação é automática |
| `last_quote_price` (numeric) | Última cotação vista |
| `last_quote_at` (timestamptz) | Quando ela foi vista |

As duas últimas fazem a carteira continuar legível se a brapi estiver fora do ar
quando o app abrir — sem elas, o cache em memória se perderia a cada reinício.

Já aplicada no Supabase.

---

## Variáveis de ambiente

```bash
MARKET_DATA_PROVIDER=brapi        # "none" desliga a busca automática
BRAPI_BASE_URL=https://brapi.dev/api
BRAPI_TOKEN=<seu token>           # segredo de servidor, nunca VITE_
BRAPI_TIMEOUT_SECONDS=12
BRAPI_MAX_RETRIES=2
BRAPI_BATCH_SIZE=10               # tickers por chamada em lote

QUOTE_CACHE_TTL_SECONDS=300       # 5 min
HISTORY_CACHE_TTL_SECONDS=3600    # 1 h
DIVIDENDS_CACHE_TTL_SECONDS=21600 # 6 h
SEARCH_CACHE_TTL_SECONDS=86400    # 24 h
QUOTE_STALE_MAX_AGE_SECONDS=86400 # até quando exibir cotação vencida
```

O token real está no `.env` (que está no `.gitignore`). O `.env.example` traz o
campo vazio.

---

## Funcionalidades

- Cotação automática ao informar o código do ativo, com sugestões enquanto digita.
- Nome do ativo preenchido a partir da cotação.
- Variação do dia por posição.
- Histórico de preço (1 mês a 5 anos) com **linha de referência no seu preço
  médio** — é o que responde "estou ganhando ou perdendo" de relance.
- Dividendos pagos, com estimativa do valor para a sua quantidade.
- Carteira consolidada: aplicado, valor atual, resultado, rentabilidade e
  distribuição por classe.
- Botão de atualizar que descarta o cache.
- Cada linha diz **de onde veio o preço**: cotação, cotação antiga, preço
  informado por você, ou preço médio na falta de tudo.
- Renda fixa e tesouro seguem com preço manual, sem ticker.

---

## Limitações da brapi encontradas

Medidas contra a API real, plano gratuito, em 11/09/2026.

| Recurso | Situação |
|---|---|
| Cotação (inclusive lote `PETR4,VALE3,ITUB4`) | ✅ funciona |
| Histórico (`range` + `interval`) | ✅ funciona |
| Dividendos (`dividends=true`) | ✅ funciona — 175 registros para PETR4 |
| Busca de tickers (`/available?search=`) | ✅ funciona |
| **Criptomoedas** | ❌ exige o plano Startup (R$ 119,99/mês) |

Outros achados que moldaram o código:

1. **Histórico e dividendos não vêm por padrão.** Só aparecem quando `range`,
   `interval` ou `dividends=true` são passados explicitamente. Sem os
   parâmetros, a resposta é idêntica à da cotação simples.
2. **Um ticker inválido derruba o lote inteiro** com 404. O provider detecta
   isso e reconsulta em separado, para não perder as cotações boas por causa de
   um código errado.
3. **Sem token a API ainda responde**, com limite de requisições menor. Por isso
   o token é opcional na configuração.
4. **Cripto falha com `FEATURE_NOT_AVAILABLE`**, não com erro genérico. O código
   trata isso como uma exceção própria e a interface avisa antes de o usuário
   tentar, em vez de deixar a chamada falhar.
5. `regularMarketTime` vem em ISO com `Z`; as datas do histórico vêm em epoch
   segundos. Formatos diferentes na mesma resposta.

---

## Cache e limite de requisições

- Cotação: 5 min. Uma carteira com 10 ativos faz **uma** chamada em lote.
- Histórico: 1 h. Dividendos: 6 h. Busca: 24 h.
- Nenhum polling: o frontend busca ao abrir a página e quando você clica em
  Atualizar. Não existe `setInterval` chamando a API.
- Cotação vencida ainda é exibida por até 24 h quando o provedor está fora,
  sempre marcada como desatualizada na interface.

O cache vive na memória do processo. Com vários workers do uvicorn, cada um tem
o seu — aceitável para dado de mercado. Para trocar por Redis, implemente
`CacheBackend` e mude o retorno de `get_cache()` em `app/core/cache.py`; nada
nos serviços muda.

---

## Como adicionar outro provedor

1. Crie a classe em `app/investments/providers/`, herdando de
   `MarketDataProvider` e implementando `get_quotes`, `get_history`,
   `get_dividends`, `search` e `capabilities`.
2. Registre em `PROVIDERS`, no `__init__.py` do pacote.
3. Aponte `MARKET_DATA_PROVIDER` no `.env` para a chave escolhida.

Nenhum serviço da carteira precisa mudar: eles só conhecem a interface.

---

## Como testar

```bash
# Unitários — não tocam a rede, usam httpx.MockTransport
cd backend
python -m pytest tests/test_brapi_provider.py tests/test_market_data.py tests/test_performance.py -v

# Contra a API real
python main.py check
python -c "
from app.investments.providers import get_market_data_provider
p = get_market_data_provider()
print('PETR4:', p.get_quote('PETR4').price)
print('busca:', [r.symbol for r in p.search('VALE')])
print('historico:', len(p.get_history('PETR4', range_='1mo')), 'pontos')
"

# Pela API, com o servidor no ar
curl -H "Authorization: Bearer <jwt>" \
  http://localhost:8000/api/v1/investments/market/PETR4/quote
```

Na interface: **Investimentos → Nova posição**, tipo *Ações*, digite `PETR4` —
as sugestões e a cotação aparecem enquanto você digita, e o nome do ativo é
preenchido sozinho. O ícone de relatório na linha abre o histórico e os
dividendos.

Para simular a API fora do ar, deixe `BRAPI_BASE_URL` apontando para um host
inválido: a carteira continua funcionando e a interface mostra o aviso de
cotações desatualizadas.

---

## O que não foi feito

| Item | Por quê |
|---|---|
| `InvestmentTransaction` (histórico BUY/SELL/DIVIDEND) | A especificação marca como "se necessário". O preço médio é informado direto; um livro de operações é uma feature própria, não um detalhe desta integração |
| Redis | A abstração está pronta; o cache em memória atende o volume atual |
| Cripto | Bloqueado pelo plano da brapi |
| Atualização em segundo plano | As cotações são buscadas sob demanda, com cache |
