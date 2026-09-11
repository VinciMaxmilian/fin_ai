# Contas remuneradas (% do CDI)

Contas que rendem um percentual do CDI — Nubank, Inter, PicPay, Mercado Pago —
têm o saldo atualizado automaticamente.

---

## Como funciona

```
Você abre o app
   ↓
GET /api/v1/accounts
   ↓
YieldService.settle()  →  credita os meses fechados que faltam
   ↓
uma transação de receita por mês, com o rendimento
```

Não existe agendador. O momento em que você abre o app é o gatilho — é o único
confiável sem um processo rodando o tempo todo. A operação é idempotente e
silenciosa: se o Banco Central estiver fora do ar, nada é creditado e o app
tenta de novo na próxima leitura.

**Por que vira transação, e não um número calculado na hora:** o saldo da conta
é derivado (`saldo inicial + transações`). Se o rendimento fosse só uma
projeção, o saldo exibido divergiria do calculado, e o extrato do app não
bateria com o do banco.

---

## O cálculo

O CDI rende **por dia útil**, sobre o **saldo daquele dia**. Por isso o cálculo
caminha dia a dia: aplica as transações do dia e só então remunera o saldo
resultante.

```
fator_do_dia = 1 + (CDI_do_dia / 100) × (percentual / 100)
```

com `100` = 100% do CDI. O rendimento entra no saldo do dia seguinte — compõe,
como nos bancos.

Consequências que os testes travam:

| Situação | Comportamento |
|---|---|
| Depósito no dia 20 | Rende só a partir do dia 20, não o mês inteiro |
| Fim de semana e feriado | Não rendem (ausentes da série do BCB) |
| Saldo zerado ou negativo | Não rende |
| Rendimento de um mês | Compõe no mês seguinte |
| 110% do CDI | Rende exatamente 1,1× o de 100% |

O mês em curso **não** é creditado — ainda está rendendo. Aparece como projeção
na tela, separado do saldo.

---

## Fonte da taxa

API de séries temporais do **Banco Central** (SGS). Pública, sem autenticação,
sem token. É a fonte oficial do CDI.

| Série | Conteúdo |
|---|---|
| 12 | CDI ao dia útil, em percentual (`0.051660` = 0,05166%) |
| 4389 | CDI anualizado (`13.90`) |

A brapi também expõe taxas, mas só no plano pago — e para um índice oficial não
faz sentido pagar por um intermediário.

### Cache

| Dado | TTL | Por quê |
|---|---|---|
| Série de mês fechado | 30 dias | Taxa passada não muda |
| Série do mês corrente | 6 h | Ainda recebe pontos a cada dia útil |
| Taxa anual | 6 h | Só para exibição |

---

## Cadastrando

**Contas → Nova conta** (ou editar). No bloco *Rendimento*, informe o **% do
CDI**: `100` para 100%, `110` para 110%. Deixe vazio se a conta não rende — é o
padrão, e o caso mais comum.

O campo **Rende desde** define a partir de quando remunerar. Meses fechados
entre essa data e hoje são creditados na primeira leitura, com teto de 24 meses
por execução para uma data antiga não gerar centenas de transações de uma vez.

---

## Proteção contra crédito duplicado

Um índice único no banco garante que o mesmo mês nunca seja creditado duas
vezes:

```sql
CREATE UNIQUE INDEX uq_transaction_yield_month
ON transaction (account_id, yield_month)
WHERE yield_month IS NOT NULL;
```

A garantia vive no banco, não na aplicação, porque é onde a corrida realmente
acontece — duas requisições simultâneas passariam por qualquer verificação feita
em Python.

---

## Variáveis de ambiente

```bash
RATE_PROVIDER=bcb                      # "none" desliga o rendimento automático
BCB_BASE_URL=https://api.bcb.gov.br
BCB_TIMEOUT_SECONDS=12
RATE_CACHE_TTL_SECONDS=21600           # 6 h
RATE_HISTORY_CACHE_TTL_SECONDS=2592000 # 30 dias
```

Nenhuma delas é segredo: a API do BCB é aberta.

---

## Arquivos

| Arquivo | O que faz |
|---|---|
| `app/rates/base.py` | `RateProvider`, `DailyRate` |
| `app/rates/bcb.py` | Cliente do SGS — o único que fala com o BCB |
| `app/rates/service.py` | Cache e tolerância a falha |
| `app/accounts/yields.py` | Cálculo e crédito |
| `tests/test_yields.py` | 11 testes do cálculo, sem rede |

Para trocar de fonte: implemente `RateProvider`, registre em `PROVIDERS` e
aponte `RATE_PROVIDER`. Nada em `yields.py` muda.

---

## Como testar

```bash
cd backend
python -m pytest tests/test_yields.py -v

# Contra o BCB real
python -c "
from datetime import date
from app.rates import RateService
s = RateService()
print('CDI anual:', s.annual_rate(), '%')
serie = s.daily_series(date(2026, 8, 1), date(2026, 8, 31))
print('agosto:', len(serie), 'dias úteis')
"
```

Na interface: crie uma conta com saldo, `100` no % do CDI e *Rende desde* alguns
meses atrás. Ao salvar e voltar para Contas, os meses fechados já aparecem
creditados em Transações como "Rendimento MM/AAAA".

---

## Limitações

| Item | Situação |
|---|---|
| Poupança | Não implementado — regra própria (70% da Selic + TR, aniversário do depósito) |
| Taxa fixa ao ano | Não implementado — o enum `YieldType` já comporta, falta uma ramificação no cálculo |
| Feriados bancários | Tratados implicitamente: dias sem CDI na série do BCB não rendem |
| IR sobre o rendimento | Não descontado. O valor creditado é bruto |
| Contas em outras moedas | Não previsto |
