# Performance

Registro do diagnóstico e do que foi feito. Data: **11/09/2026**.

---

## O sintoma

Páginas lentas. O dashboard levava **10,2 segundos**.

## O diagnóstico

Duas causas, medidas antes de mexer em qualquer coisa.

### 1. N+1 de consultas

O dashboard fazia **49 idas ao banco**, sendo 24 delas a *mesma* consulta. Cada
cartão disparava uma consulta para a fatura e outra para o limite; listagens
eram relidas três vezes na mesma requisição.

### 2. O banco está longe

Latência de rede medida daqui:

| Região | Ida e volta |
|---|---|
| **us-west-2 (Oregon) — atual** | **190 ms** |
| sa-east-1 (São Paulo) | **11 ms** |
| us-east-1 (Virgínia) | 136 ms |

Cada consulta custa uma viagem até Oregon. É isso que transforma 49 consultas em
10 segundos.

---

## Por que async não era a resposta

A pergunta natural é "não seria melhor deixar async?". Não:

> **Async serve para atender muitas requisições ao mesmo tempo. Não deixa uma
> requisição mais rápida.**

As 49 consultas eram **sequenciais**, e continuariam sequenciais em async —
`await` não paraleliza nada sozinho. Reescrever tudo para SQLAlchemy async teria
custado semanas e mantido os 10 segundos.

Async (ou threads) só ajudaria rodando consultas **independentes em paralelo**,
com `asyncio.gather`. Isso é possível, mas: entrega menos que a mudança de
região, exige reescrever a camada de banco inteira, e multiplica o uso de
conexões do pooler. Fica como opção futura, se a concorrência virar problema.

---

## O que foi feito

### Livro de compras carregado uma vez

`CardService` carregava fatura e limite por cartão. Agora carrega todas as
compras de crédito numa consulta e calcula em memória.

`app/cards/service.py` — `_ledger()`

### Memoização dentro da requisição

Listas de contas e cartões eram relidas a cada chamada. Os serviços vivem uma
requisição só, então guardar o resultado é seguro — e há `invalidate()` para o
caso de escrita no meio do caminho.

`app/cards/service.py`, `app/accounts/service.py`

### Contas lidas uma vez, filtradas em memória

Pedir "com arquivadas" e "sem arquivadas" custava duas consultas para um recorte
que o Python faz de graça.

### Somas de transação unificadas

`overview` (mês) e `cash_flow` (período) somavam a mesma tabela separadamente.
Agora uma busca cobre o maior intervalo pedido e os recortes saem de memória.

`app/reports/service.py` — `daily_type_sums()`

### Sem escrita no caminho do dashboard

A gravação da última cotação acontecia dentro do GET do dashboard. Agora só na
tela de Investimentos, que é onde importa.

`portfolio(persist_quotes=False)`

---

## Resultado

| | Antes | Depois |
|---|---|---|
| Dashboard | 49 consultas · **10,2 s** | 10 consultas · **2,1 s** |
| Cartões | 13 consultas · 2,5 s | 2 consultas · **0,37 s** |
| Contas | 4 consultas · 0,77 s | 3 consultas · **0,56 s** |

Os números conferem com os de antes — mesmas receitas, despesas e pontos de
gráfico.

---

## O que ainda está na mesa

### Mudar a região do banco — o maior ganho restante

As 10 consultas que sobraram custam **1,85 s** em Oregon e custariam **0,11 s**
em São Paulo. Sem tocar em código.

Não dá para mudar a região de um projeto existente do Supabase: é preciso criar
outro em `sa-east-1` e migrar. Com o volume atual (103 linhas) leva minutos.

```bash
# 1. Crie o projeto novo no painel, região São Paulo
# 2. Copie a connection string do Session Pooler
cd backend
python scripts/migrar_regiao.py --destino "postgresql+psycopg2://..."   # simula
python scripts/migrar_regiao.py --destino "postgresql+psycopg2://..." --executar
# 3. Atualize POSTGRES_* e SUPABASE_* no .env
# 4. python main.py check && python main.py runserver
```

O script aplica as migrations no destino, copia `auth.users` e
`auth.identities` (para os logins continuarem valendo) e todas as tabelas do
app na ordem das chaves estrangeiras. A origem não é modificada, e a cópia é
reexecutável sem duplicar.

**Sessões ativas não são copiadas** — todo mundo faz login de novo uma vez. Isso
é inevitável e desejável: os tokens antigos foram emitidos por outro projeto.

### `pool_pre_ping` custa uma ida ao banco por requisição

Medido: **186 ms**. Ele testa a conexão antes de usar, e é o que evita erro
quando o pooler derruba uma conexão ociosa.

Ficou configurável, **ligado por padrão** — 186 ms de latência é melhor que um
erro intermitente na cara do usuário:

```bash
DB_POOL_PRE_PING=false   # economiza uma ida; aceite o risco conscientemente
DB_POOL_RECYCLE=280      # recicla antes do tempo ocioso do pooler
```

Depois da mudança para São Paulo isso custa 11 ms e a discussão perde sentido.

### Consultas independentes em paralelo

Restam 10 consultas em sequência no dashboard. Rodá-las em paralelo (threads com
sessões separadas, ou async) levaria a ~3 rodadas. Só vale considerar **depois**
da mudança de região — lá, 10 consultas já custam 110 ms no total.

---

## Como medir de novo

```bash
cd backend
python - <<'EOF'
import time
from sqlalchemy import event, select
from app.database.session import SessionLocal, engine
from app.users.models import User
from app.reports.service import ReportService

consultas = []
@event.listens_for(engine, "before_cursor_execute")
def _a(c, cu, st, p, ctx, em): ctx._t0 = time.perf_counter()
@event.listens_for(engine, "after_cursor_execute")
def _d(c, cu, st, p, ctx, em): consultas.append((time.perf_counter() - ctx._t0) * 1000)

db = SessionLocal()
user = db.execute(select(User).where(User.email == "seu@email.com")).scalar_one()
t0 = time.perf_counter()
ReportService(db, user.id).dashboard("30d")
print(f"{len(consultas)} consultas | {(time.perf_counter()-t0)*1000:.0f} ms")
EOF
```

A regra que orientou tudo isto: **meça antes de otimizar.** O palpite natural
aqui era async, e teria consertado a coisa errada.
