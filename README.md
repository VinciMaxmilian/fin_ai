# La Casa Del Money

WebApp de gestão financeira pessoal. React + TypeScript no front, FastAPI +
PostgreSQL (Supabase) no back.

> Estado atual do projeto, decisões e pendências: **[STATUS.md](STATUS.md)**
> Segurança (o que protege os dados e o que não está coberto): **[docs/seguranca.md](docs/seguranca.md)**
> Integração de dados de mercado: **[docs/investimentos-brapi.md](docs/investimentos-brapi.md)**
> Contas remuneradas (% do CDI): **[docs/contas-remuneradas.md](docs/contas-remuneradas.md)**
> Performance e latência do banco: **[docs/performance.md](docs/performance.md)**
> Templates de e-mail: **[docs/email-templates/](docs/email-templates/)**

---

## Rodando local

Pré-requisitos: Python 3.11+, Node 20+.

### 1. Configuração

O `.env` da raiz já está preenchido e é compartilhado pelos dois lados (o Vite
lê as variáveis `VITE_*` de lá). Se for começar do zero, copie o exemplo:

```bash
cp .env.example .env
```

### 2. Backend

```bash
cd backend

# ambiente virtual (só na primeira vez)
python -m venv .venv
.venv/Scripts/activate          # Windows (bash)
# .venv\Scripts\activate        # Windows (PowerShell/cmd)
# source .venv/bin/activate     # macOS/Linux

pip install -r requirements-dev.txt

# confere banco e Supabase antes de subir
python main.py check

# sobe a API (aplica as migrations antes)
python main.py runserver
```

API em <http://localhost:8000> · documentação em <http://localhost:8000/docs>

Outros comandos:

```bash
python main.py migrate                      # só aplica as migrations
python main.py routes                       # lista as rotas
python main.py runserver --port 9000        # outra porta
python main.py runserver --skip-migrations  # não toca no banco
python main.py runserver --no-reload        # sem auto-reload
```

### 3. Frontend

Em outro terminal:

```bash
cd frontend
npm install
npm run dev
```

App em <http://localhost:5173>

### 4. Cotações de investimentos (opcional)

A área de Investimentos busca cotações do mercado brasileiro na
[brapi.dev](https://brapi.dev). Crie uma conta lá, pegue o token e coloque no
`.env` da raiz:

```bash
MARKET_DATA_PROVIDER=brapi
BRAPI_TOKEN=seu_token_aqui
```

O token é **segredo de servidor**: nunca use o prefixo `VITE_` nele, porque isso
o colocaria no bundle do navegador. Quem fala com a brapi é o backend.

Sem token a brapi ainda responde, com limite de requisições menor. Para desligar
a busca automática por completo, use `MARKET_DATA_PROVIDER=none` — a carteira
continua funcionando com os preços informados por você.

Confira o que o seu plano libera:

```bash
curl -H "Authorization: Bearer <jwt>"   http://localhost:8000/api/v1/investments/market/capabilities
```

### 5. Primeiro acesso

Abra <http://localhost:5173>, clique em **Criar uma conta** e cadastre-se com
e-mail e senha. As 12 categorias padrão são criadas automaticamente na primeira
requisição autenticada.

Para cadastrar um investimento: **Investimentos → Nova posição**. Informe o
código do ativo (`PETR4`, `HGLG11`, `IVVB11`) e o app busca a cotação sozinho,
preenchendo o nome. Renda fixa e tesouro não têm código — nesses casos você
informa o preço atual na mão. A cotação é atualizada quando a página abre e
quando você clica em *Atualizar*; entre uma e outra ela fica em cache por 5
minutos, para não gastar o limite de requisições da brapi.

> O projeto do Supabase exige confirmação de e-mail. Se preferir não lidar com
> isso durante o desenvolvimento, desative *Confirm email* em
> **Authentication → Providers → Email** no painel do Supabase, ou crie o
> usuário já confirmado pela API de admin.

---

## Testes

```bash
cd backend

# unitários: dinheiro, datas, faturas, recorrências
python -m pytest -q

# ponta a ponta, contra a API rodando em outro terminal
python scripts/smoke.py
```

O smoke test exercita todos os módulos (contas, cartões, transações,
parcelamento, orçamento, metas, investimentos, dashboard, relatórios e as regras
de proteção) e imprime o resultado de cada verificação.

Lint e typecheck:

```bash
cd backend  && python -m ruff check app/ scripts/
cd frontend && npm run typecheck && npm run build
```

---

## Docker

```bash
docker compose up --build
```

Frontend em <http://localhost:5173>, API em <http://localhost:8000>. O banco é o
Supabase — não subimos um Postgres local, porque o app também depende do
Supabase Auth e manter dois bancos diferentes entre desenvolvimento e produção
garante divergência de schema.

> Ainda não validei este caminho. O `python main.py runserver` é o fluxo testado.

---

## Deploy

O frontend vai para o **Netlify** (estático, configurado em `netlify.toml`) e o
backend para a **Vercel** (serverless, em `backend/vercel.json`). O banco e o
Auth continuam no Supabase nos dois ambientes.

O passo a passo — variáveis de ambiente de cada plataforma, connection string
do pooler, quando rodar as migrations e a ordem de subida — está em
[docs/deploy.md](docs/deploy.md).

---

## Arquitetura

```
Navegador                Supabase Auth
   │  login/senha, Google      │
   ├──────────────────────────>│
   │<──────── JWT (ES256) ─────┘
   │
   └── Bearer JWT ──> FastAPI ──valida via JWKS──> regra de negócio
                         │
                         └──> PostgreSQL (Supabase)
```

O FastAPI é o **único dono das regras financeiras**. Nenhum cálculo importante
vive no React — é o que permite, depois, um app iOS em Swift e um Android em
React Native consumirem exatamente o mesmo comportamento.

O Supabase cuida só de identidade. O schema `public` está fechado para as roles
`anon` e `authenticated` (RLS + `REVOKE`), então a chave pública do frontend não
abre as tabelas: todo acesso a dado passa pela API.

### Estrutura

```
backend/
├── main.py            CLI (runserver, migrate, check, routes)
├── app/
│   ├── main.py        monta a API
│   ├── core/          config, segurança, deps, erros, paginação, cache
│   ├── database/      base, sessão, registro de modelos
│   ├── auth/ users/ accounts/ cards/ categories/ transactions/
│   ├── recurring/ budgets/ goals/ installments/ reports/
│   ├── investments/
│   │   ├── providers/ MarketDataProvider + BrapiProvider
│   │   └── services/  carteira, dados de mercado, desempenho
│   └── ai/            reservado para o futuro — nada implementado
├── alembic/versions/  migrations
├── scripts/smoke.py   teste ponta a ponta
└── tests/             testes unitários

frontend/
└── src/
    ├── styles/        tokens do design system
    ├── components/    ui/ (vidro), charts/ (SVG próprio), layout/
    ├── pages/         14 telas
    ├── services/      supabase, cliente HTTP, endpoints
    ├── stores/ hooks/ types/ utils/
```

---

## Escopo desta versão

**Tem**: cadastro manual de contas, cartões, transações (receita, despesa,
transferência, parcelamento), categorias, contas recorrentes com previsão,
orçamento mensal, metas, dashboard e relatórios. Em investimentos, cotações
automáticas do mercado brasileiro via brapi.dev — a única integração externa do
projeto, e só de dados públicos de mercado.

**Não tem, de propósito**: integração bancária, Open Finance, leitura de
notificações e qualquer recurso de IA. A arquitetura está preparada para
recebê-los sem reescrita — veja `backend/app/ai/README.md`.

**Nunca vai ter**: acesso às suas credenciais bancárias. Todos os dados são
informados por você.
