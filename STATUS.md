# Relatório de situação — WebApp de gestão financeira

Última atualização: **11/09/2026**

---

## Resumo

O projeto está **funcionando ponta a ponta** contra o Supabase real: login, API,
banco, dashboard e todos os módulos financeiros. Backend e frontend passam em
typecheck, lint e build.


| Verificação                   | Resultado                           |
| ----------------------------- | ----------------------------------- |
| Testes unitários do backend   | **26 passando** (`pytest`)          |
| Teste de fumaça ponta a ponta | **39 verificações, 0 falhas**       |
| Lint do backend (ruff F,E9)   | limpo                               |
| Typecheck do frontend (`tsc`) | limpo                               |
| Build do frontend             | ok (3 chunks, 209 kB gzip no total) |
| Rotas da API                  | 38                                  |
| Tabelas criadas no Supabase   | 11                                  |


---



## Decisões tomadas no caminho



### 1. Supabase Auth como provedor de identidade

Você escolheu essa opção. O FastAPI **não guarda senha**: valida o JWT do
Supabase via JWKS (ES256) e cria o perfil local na primeira requisição
autenticada. Ganhamos de graça confirmação de e-mail, reset de senha, refresh
token e SDKs oficiais para iOS/React Native no futuro.

### 2. O host do banco que você passou não funciona nesta rede

`db.hqmtxzfakmuubvvhgzma.supabase.co` resolve **só para IPv6**, e esta máquina
(e o Docker com a configuração padrão) não alcança IPv6. Fiz uma varredura em
todas as regiões do pooler e encontrei o projeto:

```
aws-0-us-west-2.pooler.supabase.com:5432
usuário: postgres.hqmtxzfakmuubvvhgzma
```

É isso que está no `.env`. A string original está registrada lá em comentário.

### 3. Fechei um buraco de segurança do Supabase

O Supabase publica o schema `public` como API REST usando a chave **anon**, que
é pública (vai no bundle do frontend). Antes da correção, um `GET` em
`/rest/v1/transaction` com aquela chave retornava **200** — ou seja, dava para
ler e escrever nas tabelas financeiras direto, ignorando toda a regra de negócio
do FastAPI.

A migration `20260911_1040_blindagem_supabase.py` aplica duas travas:

1. RLS ligada (`ENABLE` + `FORCE`) em todas as 10 tabelas, sem nenhuma policy →
  o Postgres nega tudo para quem não tem `BYPASSRLS`.
2. `REVOKE ALL` das roles `anon` e `authenticated`, incluindo `DEFAULT
  PRIVILEGES`, para tabelas futuras já nascerem fechadas.

Também adiciona `app_user.id → auth.users(id) ON DELETE CASCADE`, para excluir a
conta no Supabase levar junto os dados financeiros.

**Depois da correção, as mesmas requisições retornam 401.** O backend conecta
como `postgres` (tem `BYPASSRLS`) e continua funcionando.

> ⚠️ Se um dia o app passar a conectar com uma role comum em vez de `postgres`,
> será preciso criar policies explícitas por `user_id` **antes** de trocar.



### 4. As cores dos gráficos foram trocadas por uma paleta validada

Minhas cores iniciais **reprovaram** no validador de paletas (faixa de
luminosidade e contraste). Troquei pela paleta de referência, que passa nos dois
temas:

- claro: separação para daltonismo ΔE 9.1 · visão normal ΔE 19.6
- escuro: ΔE 8.4 · ΔE 19.3 · todas acima de 3:1 de contraste

A paleta tem **8 posições** e existem 9 categorias de despesa, então duas duplas
compartilham matiz (Transporte/Viagens e Educação/Assinaturas). Isso é aceitável
porque **todo gráfico de categoria é uma lista de barras com nome e valor
escritos em cada linha** — a cor reforça, nunca carrega a identidade sozinha.
Uma nona cor cairia abaixo do piso de croma e viraria cinza.

Está tudo documentado em `frontend/src/components/charts/palette.ts`.

---



## ⚠️ Ação necessária da sua parte

1. **Rotacione os segredos.** Você colou no chat a senha do banco e a
  `service_role` key (que ignora RLS e dá acesso total). Troque as duas no
   painel do Supabase e atualize o `.env`.
2. **Habilite o Google OAuth** se quiser usá-lo. Está **desativado** no projeto
  hoje (confirmei em `/auth/v1/settings`). O botão já existe na tela de login e
   passa a funcionar assim que você configurar o provider no painel com as
   credenciais do Google Cloud. Sem isso, ele retorna "provider is not enabled".
3. O `.env` está no `.gitignore` e **não** foi commitado. O `.env.example` não
  contém nenhum segredo real.

---



## O que está pronto



### Backend — `backend/`

Estrutura modular, um pacote por domínio, cada um com `models / schemas / service / router`:

```
app/
├── main.py           monta a API e registra os routers
├── core/             config, segurança (JWT), deps, erros, paginação,
│                     service base, aritmética de datas e dinheiro
├── database/         base declarativa, sessão, registro de modelos
├── auth/             /auth/config e /auth/session
├── users/            perfil local espelhando o auth.users
├── accounts/         contas + saldo derivado
├── cards/            cartões, faturas, limite
├── categories/       categorias + seed padrão
├── transactions/     lançamentos, filtros, parcelamento
├── recurring/        regras recorrentes e previsão de ocorrências
├── budgets/          orçamento mensal com realizado
├── goals/            metas e aportes
├── installments/     planos de parcelamento
├── investments/      carteira e distribuição
├── reports/          dashboard e todos os relatórios
└── ai/               camada reservada (NADA implementado)
```

Pontos de regra de negócio que valem destacar:

- **Saldo da conta é derivado**, nunca armazenado: `saldo inicial + receitas − despesas − transferências enviadas + transferências recebidas`. Compras no
cartão não entram (afetam a fatura, não a conta).
- **Fatura do cartão**: compra depois do dia de fechamento entra na fatura
seguinte; vencimento cai no mês seguinte quando o dia de vencimento vem antes
do de fechamento; dia 31 encolhe para o último dia do mês. Coberto por testes.
- **Parcelamento**: a divisão preserva os centavos — a sobra do arredondamento
vai para a primeira parcela, como fazem as operadoras.
- **Isolamento entre usuários**: toda leitura e escrita passa por
`OwnedResourceService`, que filtra por `user_id`. É impossível um endpoint novo
esquecer o filtro.
- **Transferências não contam** como receita nem despesa nos relatórios.
- **Proteções**: conta com transações não pode ser excluída (só arquivada);
categoria padrão não pode ser excluída; categoria em uso exige recategorizar.



### Frontend — `frontend/`

```
src/
├── styles/              tokens.css (design system) + global.css
├── components/
│   ├── ui/              GlassCard, GlassPanel, GlassModal, GlassButton,
│   │                    GlassInput/Select/Textarea, Toast, Skeleton,
│   │                    EmptyState, ErrorNotice, Badge, Progress, Stat,
│   │                    Segmented, Icon (42 ícones inline)
│   ├── charts/          TrendChart (linha/área com crosshair + tooltip),
│   │                    GroupedBars, BarList, StackedBar, palette.ts
│   └── layout/          AppLayout, Sidebar, navigation.ts
├── pages/               14 páginas
├── services/            supabase.ts, client.ts, endpoints.ts
├── stores/              auth.tsx
├── hooks/               useAsync, useAction, useTheme, useDebounced,
│                        useElementWidth
├── types/               api.ts (espelho dos schemas do backend)
└── utils/               format.ts, cx.ts
```

**14 páginas**: Login, Dashboard, Contas, Cartões, Transações, Categorias,
Contas recorrentes, Orçamento, Metas, Parcelamentos, Investimentos, Patrimônio,
Relatórios, Configurações.

**Design**: superfícies de vidro em 3 níveis de profundidade, paleta neutra com
cor só onde carrega significado, tema claro/escuro, cantos arredondados, sombras
em camadas, animações discretas. Responsivo de verdade — sidebar no desktop,
sidebar compacta no tablet, barra inferior com botão central no celular (não é a
tela de desktop espremida).

Dependências do frontend: apenas `react`, `react-dom`, `react-router-dom` e
`@supabase/supabase-js`. Os gráficos são SVG próprio, sem biblioteca.

### Preparado para o futuro (sem implementar)

- `app/ai/provider.py` — contrato `AIProvider` e `NullProvider` que recusa
explicitamente. `app/ai/README.md` explica como plugar Gemini/OpenAI/LLM local.
- Backend 100% independente do frontend: React, iOS e Android consomem a mesma
API REST.
- Nenhuma regra financeira vive no React.

---



## O que **não** está feito


| Item                          | Situação                                                                         |
| ----------------------------- | -------------------------------------------------------------------------------- |
| Google OAuth                  | Código pronto; falta habilitar o provider no painel do Supabase                  |
| Pagamento de fatura de cartão | Não modelado — faturas vencidas são tratadas como pagas no cálculo do limite     |
| Histórico de cotações         | A evolução do patrimônio usa o valor de hoje dos investimentos em todos os meses |
| Testes de integração da API   | Existe o smoke test; não há testes de endpoint com banco de teste isolado        |
| Testes do frontend            | Nenhum                                                                           |
| CI                            | Nenhum                                                                           |
| `docker compose up`           | Escrito, **não executado** — não cheguei a validar o build das imagens           |


---



## Arquivos de referência rápida


| Preciso de…                       | Está em                                                        |
| --------------------------------- | -------------------------------------------------------------- |
| Tokens do design                  | `frontend/src/styles/tokens.css`                               |
| Paleta dos gráficos e a validação | `frontend/src/components/charts/palette.ts`                    |
| Regra de fatura do cartão         | `backend/app/cards/service.py`                                 |
| Divisão de parcelas               | `backend/app/core/money.py`                                    |
| Previsão de recorrências          | `backend/app/recurring/service.py`                             |
| Dashboard e relatórios            | `backend/app/reports/service.py`                               |
| Isolamento por usuário            | `backend/app/core/service.py`                                  |
| Blindagem do Supabase             | `backend/alembic/versions/20260911_1040_blindagem_supabase.py` |


  
E algo mais que é para adicionar:  
  
1. Deixar a sidebar expandivel e reprimivel  
2. Seguir esse prompt:  
  
---

# Integração brapi.dev — **implementada**

A especificação que estava aqui foi executada. Relatório completo, com arquivos,
endpoints, migration, variáveis de ambiente, limitações da API e como testar:

**[docs/investimentos-brapi.md](docs/investimentos-brapi.md)**

Resumo: cotações, histórico, dividendos e busca de tickers do mercado brasileiro,
com cache e tolerância a queda do provedor. Toda a comunicação com a brapi
acontece no backend — o token nunca chega ao navegador. Criptomoedas ficaram de
fora porque exigem plano pago na brapi.

Números depois da integração: **69 testes** (eram 26), **27 verificações ponta a
ponta** contra a API real, lint e typecheck limpos.
