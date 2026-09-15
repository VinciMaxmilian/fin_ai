# Deploy — frontend no Netlify, backend na Vercel

O projeto vai para o ar em duas plataformas diferentes, ligadas por duas
configuracoes: o frontend precisa saber a URL da API (`VITE_API_URL`) e o
backend precisa autorizar a origem do frontend (`CORS_ORIGINS`). Se algo
funcionar local e quebrar em producao, comece por essas duas.

O banco e o Auth continuam no Supabase, iguais em qualquer ambiente.

```
Netlify (estatico)            Vercel (serverless)          Supabase
  React + Vite    ──fetch──▶    FastAPI           ──SQL──▶   Postgres
                                                 ──JWKS──▶   Auth
```

---

## 1. Backend na Vercel

URL do projeto: <https://fin-ai-ten-inky.vercel.app>

> Essa URL e gerada pela Vercel e **muda se o projeto for recriado** -- ja mudou
> uma vez (`fin-ai-three-pearl` -> `fin-ai-ten-inky`). Isso importa mais do que
> parece: a `VITE_API_URL` e embutida no bundle **durante o build** do Netlify,
> entao uma troca de URL derruba o frontend em producao e so volta com um novo
> deploy la. Um dominio proprio na Vercel elimina o problema de vez.

### Como a API vira uma serverless function

`backend/api/index.py` expoe um objeto ASGI chamado `app` e o `backend/vercel.json`
manda **todas** as rotas para esse arquivo. A Vercel serve o ASGI direto — nao ha
handler para escrever, e nenhum caminho da API precisa ser listado.

O `vercel.json` usa `builds` + `routes` (e nao `functions` + `rewrites`) porque
`routes` preserva o caminho original da requisicao. Com `rewrites`, o que chega
ao ASGI e o caminho de **destino** (`/api/index`): nenhuma rota do FastAPI casa
e a API inteira responde `{"detail":"Not Found"}`, inclusive o `/health`.

Como consequencia dessa escolha, `maxDuration` nao pode ser declarado (a chave
`functions` nao convive com `builds`); vale o timeout padrao do plano. Se um dia
precisar de mais, ajuste em Project Settings → Functions.

### Criando o projeto

1. Importe o repositorio em <https://vercel.com/new>.
2. **Root Directory: `backend`** — este e o passo que as pessoas esquecem. Sem
   ele a Vercel nao acha `requirements.txt` nem `vercel.json`.
3. Framework Preset: **Other**. Nao ha build step; o `requirements.txt` e
   instalado automaticamente.
4. Deploy.

A versao do Python vem do runtime padrao da Vercel (3.12 hoje). Se precisar
fixar, use Project Settings → General.

### Variaveis de ambiente (Project Settings → Environment Variables)

Use a **connection string do pooler** do Supabase, porta **6543** (Dashboard →
Project Settings → Database → Connection pooling, modo *Transaction*). A porta
5432 e conexao direta: em serverless ela esgota o limite de conexoes do projeto.

| Variavel | Valor |
| --- | --- |
| `DATABASE_URL` | `postgresql+psycopg2://postgres.<ref>:<senha>@<host>.pooler.supabase.com:6543/postgres` |
| `ENVIRONMENT` | `production` |
| `DEBUG` | `false` |
| `SUPABASE_URL` | `https://<ref>.supabase.co` |
| `SUPABASE_ANON_KEY` | chave `anon` |
| `SUPABASE_SERVICE_KEY` | chave `service_role` — **segredo**, nunca no frontend |
| `CORS_ORIGINS` | `https://lacasadelmoney.netlify.app` (virgula separa varias) |
| `CORS_ORIGIN_REGEX` | opcional: `https://.*--lacasadelmoney\.netlify\.app` para liberar os deploy previews e branch deploys |
| `BRAPI_TOKEN` | token da brapi.dev — **segredo** |

O prefixo `postgresql+psycopg2://` importa: e o dialeto que o SQLAlchemy espera.
A string que o Supabase mostra comeca com `postgresql://`; troque o esquema.

`DB_DISABLE_POOL` nao precisa ser definida — o backend detecta a variavel
`VERCEL` e usa `NullPool` sozinho, deixando o reuso de conexoes com o pooler do
Supabase (ver `backend/app/database/session.py`).

### Migrations

**Nao rodam no deploy.** Varias instancias da function sobem em paralelo e
aplicar Alembic em todas seria uma corrida. Rode da sua maquina, apontando para
o banco de producao, **antes** de publicar uma mudanca de schema:

```bash
cd backend
DATABASE_URL="postgresql+psycopg2://...pooler.supabase.com:6543/postgres" \
  .venv/Scripts/python.exe main.py migrate
```

### Conferindo

```bash
curl https://fin-ai-ten-inky.vercel.app/health
# {"status":"ok","environment":"production"}
```

Se o `environment` vier `development`, as variaveis nao foram aplicadas.

A raiz (`/`) responde com um indice apontando para `/docs`, `/health` e o prefixo
da API. A documentacao interativa fica em `/docs`; o esquema cru, em
`/openapi.json`.

---

## 2. Frontend no Netlify

O `netlify.toml` na raiz ja traz build, publish, o redirect de SPA e os headers
de cache. No painel basta confirmar que a configuracao foi lida.

1. **Add new site → Import an existing project**, escolha o repositorio.
2. Nao mexa em build command nem publish directory: o `netlify.toml` manda.
3. Defina as variaveis abaixo em **Site settings → Environment variables**.
4. Deploy.

### Variaveis de ambiente

| Variavel | Valor |
| --- | --- |
| `VITE_API_URL` | `https://fin-ai-ten-inky.vercel.app/api/v1` |
| `VITE_SUPABASE_URL` | `https://<ref>.supabase.co` |
| `VITE_SUPABASE_ANON_KEY` | chave `anon` |

Inclua o sufixo `/api/v1` na `VITE_API_URL` — o cliente concatena os caminhos
direto nela (`backend/../frontend/src/services/client.ts`).

Tudo que comeca com `VITE_` e **embutido no bundle** durante o build e fica
visivel para qualquer visitante. Sao valores publicos por definicao; a chave
`service_role` e o `BRAPI_TOKEN` ficam so na Vercel. Trocar uma dessas
variaveis exige um **redeploy** — nao basta salvar no painel.

### Por que o redirect de SPA

O React Router resolve as rotas no cliente. Sem a regra `/* → /index.html 200`,
abrir `https://seu-site.netlify.app/transacoes` direto (ou recarregar a pagina)
devolve 404, porque nao existe esse arquivo no disco.

---

## 3. Depois do primeiro deploy

A ordem importa: a URL do Netlify so existe depois que o site sobe.

1. Publique o backend e anote a URL da Vercel.
2. Publique o frontend com `VITE_API_URL` apontando para ela.
3. Volte na Vercel e coloque a URL do Netlify em `CORS_ORIGINS`. **Redeploy** —
   variaveis de ambiente so valem a partir do proximo deploy.
4. No Supabase, em **Authentication → URL Configuration**, adicione a URL do
   Netlify em *Site URL* e em *Redirect URLs*. Sem isso o login por email e o
   OAuth voltam para `localhost`.

## URLs em producao

| Peca | URL |
| --- | --- |
| Frontend (Netlify) | <https://lacasadelmoney.netlify.app> |
| Backend (Vercel) | <https://fin-ai-ten-inky.vercel.app> |
| `VITE_API_URL` no Netlify | `https://fin-ai-ten-inky.vercel.app/api/v1` |
| `CORS_ORIGINS` na Vercel | `https://lacasadelmoney.netlify.app` |

Sem barra no fim: o header `Origin` do navegador nunca a envia, e o
`allow_origin_regex` do Starlette compara com `fullmatch`. O validador em
`app/core/config.py` corta a barra caso ela venha colada do painel.

## Problemas comuns

| Sintoma | Causa provavel |
| --- | --- |
| **Toda** rota devolve `{"detail":"Not Found"}`, ate `/health` | O ASGI esta recebendo `/api/index` em vez do caminho original — `vercel.json` voltou para `rewrites` |
| `/health` responde `"environment":"development"` | Nenhuma variavel de ambiente configurada na Vercel: o app subiu so com os defaults do codigo |
| `CORS policy: No 'Access-Control-Allow-Origin'` | URL do Netlify fora de `CORS_ORIGINS`, ou a variavel mudou sem redeploy |
| Frontend chama `localhost:8000` em producao | `VITE_API_URL` ausente no build — defina e refaca o deploy |
| 404 ao recarregar uma rota interna | Redirect de SPA nao aplicado; confira se o `netlify.toml` foi lido |
| `remaining connection slots are reserved` | `DATABASE_URL` na porta 5432 em vez da 6543 do pooler |
| Login redireciona para `localhost` | Redirect URLs do Supabase nao atualizadas |
| 500 logo apos deploy de schema | Migration nao aplicada — rode `python main.py migrate` |
