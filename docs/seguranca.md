# Segurança

O que sustenta o aviso "Conexão criptografada. Seus dados são privados e
visíveis apenas por você." que aparece no login e no rodapé das páginas.

Cada afirmação abaixo corresponde a um mecanismo verificável no código. Se um
deles for removido, o aviso passa a ser falso — este documento existe para que
essa relação fique explícita.

## Identidade

O backend **nunca vê nem armazena senhas**. Login, cadastro e recuperação
acontecem no Supabase Auth; o app recebe um JWT e o envia em
`Authorization: Bearer <token>`.

`app/core/security.py` valida, em toda requisição:

| Verificação | Por quê |
|---|---|
| Assinatura (JWKS ES256/RS256, ou HS256 legado) | Token forjado não passa |
| `iss` (emissor) | Token de outro projeto Supabase não passa |
| `aud` (audiência) | Token emitido para outro público não passa |
| Expiração | Sessão vencida não passa |
| Algoritmo contra lista fixa | Impede a troca de algoritmo (`alg: none`) |

O fluxo OAuth usa **PKCE** (`services/supabase.ts`).

## Isolamento entre contas

Duas barreiras independentes, porque uma só depende de ninguém errar:

1. **Na aplicação** — todo acesso a dado de usuário passa por
   `OwnedResourceService` (`app/core/service.py`), cuja consulta base já nasce
   com `WHERE user_id = <usuário do token>`. Um endpoint novo que esqueça o
   filtro não compila um caminho alternativo: não existe consulta sem escopo.
2. **No banco** — a migration `20260911_1040_blindagem_supabase` liga
   `ROW LEVEL SECURITY` (com `FORCE`) em todas as tabelas e **revoga** os
   privilégios das roles `anon` e `authenticated`. Sem isso, a chave anon — que
   por definição é pública, vai no bundle — leria as tabelas direto pelo
   PostgREST, passando por cima de toda a regra de negócio.

Consequência prática: pedir o recurso de outra pessoa pelo ID devolve
`404 não encontrado`, não os dados dela.

## Transporte e armazenamento

- Conexão ao banco com `sslmode=require` (`app/database/session.py`).
- `Strict-Transport-Security` obriga HTTPS fora de desenvolvimento.
- `Cache-Control: no-store` em toda resposta da API: dado financeiro não fica
  no disco do navegador nem em cache de proxy.
- Ao excluir a conta no Supabase Auth, os dados financeiros vão junto
  (`ON DELETE CASCADE` em `app_user.id → auth.users.id`).

## Defesas contra ataque

| Ataque | Defesa |
|---|---|
| SQL injection | SQLAlchemy com parâmetros ligados; nenhuma query montada por concatenação |
| XSS | React escapa por padrão; nenhum `dangerouslySetInnerHTML` no projeto; CSP sem `unsafe-inline`/`unsafe-eval` em `script-src` |
| CSRF | A sessão viaja em header `Authorization`, não em cookie, e o CORS roda com `allow_credentials=False` — o navegador nunca anexa credencial a uma chamada entre origens |
| Clickjacking | `frame-ancestors 'none'` + `X-Frame-Options: DENY` |
| IDOR | Escopo por `user_id` + RLS (acima) |
| Força bruta / abuso | Limite por cliente (`app/core/middleware.py`); o Supabase aplica o próprio limite no login |
| SSRF / manipulação da URL de saída | Código de ativo restrito a `^[A-Za-z0-9.^=-]{1,16}$` em três camadas: rota, schema e provedor (`app/investments/tickers.py`) |
| MIME sniffing | `X-Content-Type-Options: nosniff` |

## Onde ficam os cabeçalhos

Estão em três lugares porque são três servidores diferentes:

- **API** — `app/core/middleware.py` (`SecurityHeadersMiddleware`).
- **Frontend no Netlify** — `dist/_headers`, gerado no build por
  `frontend/build/security-headers.ts`. É gerado, e não escrito à mão, porque
  `connect-src` precisa das URLs reais da API e do Supabase, que mudam por
  ambiente. CSP errada falha em silêncio.
- **Frontend no Docker** — `frontend/nginx.conf`, com a CSP injetada pelo
  `Dockerfile` a partir das mesmas variáveis do build.

Conferir o que foi gerado: `npm run build && cat dist/_headers`.

## Limites conhecidos

Honestidade sobre o que **não** está coberto hoje:

- **O limite de requisições vive na memória do processo.** Em serverless
  (Vercel), cada instância tem o próprio contador, então o teto efetivo é por
  instância. Corta o abuso de um cliente em loop, que é o caso comum; não
  substitui um WAF contra ataque distribuído. Trocar por Redis é mudar a classe
  `_SlidingWindow`.
- **O token da sessão fica no `localStorage`** (padrão do supabase-js). Um XSS o
  leria. É por isso que `script-src 'self'` — sem `unsafe-inline` — importa: ele
  é a barreira que impede o XSS de acontecer.
- **Não há trilha de auditoria** de quem leu ou alterou o quê.
- **Não há criptografia em repouso a nível de aplicação.** O disco do Supabase é
  cifrado, mas o backend enxerga os valores em claro — necessário para somar,
  filtrar e gerar relatórios.
- **`SUPABASE_SERVICE_KEY` não é usada por nenhum código.** Enquanto estiver no
  `.env`, é uma chave com poder total sem nenhuma função. Recomendado remover.

## Rotina de manutenção

```bash
# Vulnerabilidades conhecidas nas dependências
cd frontend && npm audit
cd backend && pip list --outdated

# Os testes que protegem estas defesas de regressão
cd backend && pytest tests/test_security.py
```

Pendência atual: `react-router-dom` 6.28 tem dois avisos moderados
(GHSA-wrjc-x8rr-h8h6, GHSA-337j-9hxr-rhxg). **Nenhum dos dois é explorável
aqui**: o primeiro exige um destino de navegação controlado pelo usuário, e
todos os destinos do app são literais fixos; o segundo só atinge hidratação SSR,
e este app é uma SPA pura. A correção exige subir para a v7, que é *breaking*.
