Claro. Eu montaria um prompt já pensando em **gerar o projeto inteiro**, mas deixando a arquitetura preparada para a IA entrar depois.

Você pode passar o prompt abaixo para Claude Code, Cursor, Windsurf ou outro agente de código:

---

# Prompt — WebApp de Gestão Financeira

Quero desenvolver um **WebApp de gestão financeira pessoal**, inicialmente **sem IA**, mas com arquitetura preparada para receber recursos de IA futuramente.

## Objetivo

Criar um aplicativo financeiro moderno onde o usuário consiga centralizar sua vida financeira em um único lugar.

A primeira versão deve funcionar **100% sem integração bancária automática e sem IA**. O usuário cadastra e organiza seus dados manualmente.

No futuro, o projeto receberá:

- IA para análise financeira
- IA para organização automática
- leitura de notificações bancárias no aplicativo mobile
- integração com bancos/Open Finance
- aplicativo iOS em Swift
- aplicativo Android em React Native
- eventualmente um modelo de IA local

**Não implementar essas funcionalidades agora.** Apenas estruturar o projeto para que possam ser adicionadas posteriormente sem necessidade de reescrever o sistema.

---



# Stack



### Frontend

- React
- TypeScript
- Vite
- CSS moderno
- Componentização
- Responsive design



### Backend

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Pydantic



### Infraestrutura

- Docker/Docker Compose
- `.env` para configurações
- API REST bem estruturada

Evitar dependências desnecessárias.

---



# Design / UI

O visual deve ser inspirado na linguagem visual dos produtos mais recentes da Apple, especialmente **macOS 26/27**, mantendo identidade própria e **sem copiar literalmente elementos proprietários**.

Referência principal:

[Figma Community — macOS 27 UI Kit](https://www.figma.com/pt-br/comunidade/file/1651309434229735362/macos-27?utm_source=chatgpt.com)

Também usar como referência visual o screenshot fornecido junto deste prompt.

O screenshot mostra a direção estética desejada:

- superfícies translúcidas
- efeito glassmorphism
- transparência
- blur
- profundidade através de camadas
- bordas suaves
- cantos bastante arredondados
- sombras extremamente suaves
- aparência premium
- bastante espaço negativo
- tipografia limpa
- ícones minimalistas
- animações discretas
- componentes parecendo "flutuar" sobre o ambiente
- aparência semelhante a interfaces recentes da Apple

**Não quero uma cópia do macOS.**

Quero que o aplicativo pareça um produto financeiro moderno que poderia fazer parte do ecossistema Apple.

O design deve funcionar tanto em:

- desktop
- notebook
- tablet
- celular

---



# Direção visual

Criar um sistema de design próprio.

### Cores

Priorizar:

- branco
- cinza muito claro
- cinza
- preto
- tons neutros

Usar cores de destaque somente quando fizer sentido.

Por exemplo:

- verde → dinheiro positivo / receita
- vermelho → despesas / valores negativos
- azul → informações
- laranja → alertas

Não transformar a interface em um aplicativo extremamente colorido.

---



# Glass UI

Criar componentes reutilizáveis para superfícies de vidro:

```text
GlassCard
GlassPanel
GlassModal
GlassButton
GlassInput
GlassNavbar
GlassSidebar
```

Usar:

```css
backdrop-filter
background: rgba(...)
border
box-shadow
border-radius
```

Mas evitar exagerar no blur.

A interface precisa continuar extremamente legível.

---



# Estrutura principal

O aplicativo deve possuir uma navegação lateral no desktop e navegação adaptada para mobile.

Menu:

```text
Dashboard

Finanças
 ├── Contas
 ├── Cartões
 ├── Transações
 ├── Categorias
 └── Contas recorrentes

Planejamento
 ├── Orçamento
 ├── Metas
 └── Parcelamentos

Patrimônio
 ├── Investimentos
 └── Patrimônio

Relatórios

Configurações
```

---



# Dashboard

O Dashboard é a tela mais importante.

Deve apresentar uma visão geral da situação financeira.

Exemplo:

```text
Olá 👋

Visão geral

Patrimônio
R$ 12.480,32

Saldo disponível
R$ 3.842,10

Receitas
R$ 4.500,00

Despesas
R$ 2.731,82
```

Depois:

### Gráfico de fluxo financeiro

Mostrar:

- receitas
- despesas
- saldo

Permitir alterar período:

```text
7 dias
30 dias
3 meses
6 meses
1 ano
```



### Despesas por categoria

Exemplo:

```text
Alimentação       R$ 620
Transporte        R$ 310
Moradia           R$ 900
Lazer             R$ 280
Assinaturas       R$ 150
Outros            R$ 471
```



### Próximas contas

```text
Hoje
Internet       R$ 99,90

15/09
Cartão         R$ 820,00

20/09
Aluguel        R$ 1.200,00
```



### Cartões

Mostrar:

```text
Cartão Itaú

Fatura atual
R$ 820,32

Limite
R$ 2.500

Disponível
R$ 1.679,68

Vencimento
10/09
```

---



# Contas bancárias

Permitir cadastrar contas.

Campos:

```text
Nome
Banco
Tipo
Saldo inicial
Saldo atual
Conta corrente / poupança / investimento
Cor ou ícone
```

Importante:

**Não implementar acesso às credenciais bancárias.**

Nesta primeira versão, todas as informações são inseridas pelo usuário.

---



# Cartões

Permitir cadastrar:

```text
Nome
Banco
Bandeira
Limite
Limite disponível
Dia de fechamento
Dia de vencimento
Conta associada
```

Também permitir acompanhar:

- compras
- parcelas
- fatura atual
- próximas faturas

---



# Transações

Criar sistema completo de transações.

Cada transação deve possuir:

```text
ID
Tipo
Valor
Descrição
Categoria
Data
Conta
Cartão
Parcelamento
Observação
Criada em
Atualizada em
```

Tipos:

```text
Receita
Despesa
Transferência
```

Possibilitar:

- criar
- editar
- excluir
- pesquisar
- filtrar
- ordenar
- categorizar

Filtros:

```text
Data
Categoria
Conta
Cartão
Tipo
Valor
```

---



# Categorias

Criar categorias personalizáveis.

Categorias iniciais:

```text
Moradia
Alimentação
Transporte
Saúde
Educação
Lazer
Assinaturas
Compras
Viagens
Investimentos
Salário
Outros
```

O usuário poderá criar suas próprias categorias.

---



# Contas recorrentes

Permitir cadastrar despesas e receitas recorrentes.

Exemplo:

```text
Aluguel
R$ 1.200
Todo dia 5

Internet
R$ 99,90
Todo dia 10

Salário
R$ 4.500
Todo dia 5
```

O sistema deve gerar/prever as próximas ocorrências.

---



# Orçamento

Criar orçamento mensal.

Exemplo:

```text
Orçamento de Setembro

Alimentação
R$ 700 / R$ 620

Lazer
R$ 300 / R$ 280

Transporte
R$ 400 / R$ 310
```

Mostrar visualmente quanto já foi utilizado.

---



# Metas

Permitir criar objetivos financeiros.

Exemplo:

```text
Reserva de emergência

Objetivo
R$ 10.000

Atual
R$ 3.200

Progresso
32%
```

Outros exemplos:

```text
Comprar computador
Viagem
Carro
Reserva
Investimentos
```

---



# Parcelamentos

Permitir registrar compras parceladas.

Exemplo:

```text
Notebook

12x R$ 350

Parcela atual:
4/12

Restante:
R$ 2.800
```

O sistema deve conseguir refletir essas parcelas nas próximas faturas/períodos.

---



# Investimentos

Criar uma área simples para patrimônio.

Não precisa de integração automática.

Permitir cadastrar:

```text
Ativo
Tipo
Quantidade
Preço médio
Valor atual
Instituição
```

Tipos:

```text
Ações
FIIs
Cripto
Renda fixa
Tesouro
ETF
Outros
```

Mostrar:

```text
Patrimônio investido
Rentabilidade
Distribuição por classe
```

---



# Relatórios

Criar relatórios visuais.

Exemplos:

### Gastos por categoria



### Evolução do patrimônio



### Receitas x despesas



### Evolução mensal



### Gastos com cartão



### Gastos recorrentes



### Investimentos

Os gráficos devem seguir o mesmo estilo minimalista do restante da aplicação.

---



# Autenticação

Preparar autenticação de usuário.

Inicialmente:

- email/senha
- Google OAuth

A arquitetura deve permitir posteriormente adicionar outros providers.

Cada usuário deve possuir seus próprios dados.

**Nunca misturar dados entre usuários.**

---



# Backend

Organizar o FastAPI de maneira modular.

Exemplo:

```text
backend/
├── app/
│   ├── main.py
│   ├── core/
│   ├── auth/
│   ├── users/
│   ├── accounts/
│   ├── cards/
│   ├── transactions/
│   ├── categories/
│   ├── recurring/
│   ├── budgets/
│   ├── goals/
│   ├── installments/
│   ├── investments/
│   ├── reports/
│   └── database/
├── tests/
├── requirements.txt
└── Dockerfile
```

Frontend:

```text
frontend/
├── src/
│   ├── components/
│   ├── pages/
│   ├── layouts/
│   ├── hooks/
│   ├── services/
│   ├── stores/
│   ├── types/
│   ├── utils/
│   └── styles/
├── public/
├── package.json
└── vite.config.ts
```

---



# Arquitetura preparada para IA

**Não implementar IA agora.**

Entretanto, deixar uma camada preparada:

```text
backend
   │
   ├── financial services
   ├── reports
   ├── authentication
   └── AI service ← futuro
```

No futuro:

```text
AI Service
    │
    ├── Gemini
    ├── OpenAI
    ├── Local LLM
    └── outros providers
```

A IA futuramente poderá utilizar ferramentas como:

```text
get_transactions()
get_balance()
get_income()
get_expenses()
get_budgets()
get_goals()
get_investments()
create_transaction()
update_category()
generate_report()
```

Mas **não criar essas ferramentas agora**, apenas deixar a arquitetura fácil de expandir.

---



# Preparação para aplicativo mobile

O backend deve ser completamente independente do frontend.

Não criar lógica financeira importante exclusivamente no React.

A regra deve ser:

```text
React/Vite
     ↓
REST API
     ↓
FastAPI
     ↓
PostgreSQL
```

Isso permitirá futuramente:

```text
             ┌── Web
             │
             ├── iOS / Swift
             │
             └── Android / React Native
                     │
                     ▼
                  FastAPI
                     │
                 PostgreSQL
```

---



# Futuro: notificações bancárias

Não implementar agora.

Mas a arquitetura deve permitir posteriormente um módulo:

```text
Mobile
   ↓
Notification Listener
   ↓
Transaction Parser
   ↓
Backend
   ↓
Transaction
```

Exemplo futuro:

```text
"Compra aprovada no valor de R$ 47,90
no estabelecimento X"
```

poderá virar:

```json
{
  "type": "expense",
  "amount": 47.90,
  "merchant": "X"
}
```

Depois poderá ser categorizado automaticamente.

---



# UX

Quero uma experiência extremamente simples.

O usuário deve conseguir:

```text
abrir aplicativo
     ↓
ver situação financeira
     ↓
entender onde está gastando
     ↓
tomar uma decisão
```

Evitar telas lotadas.

Priorizar:

- hierarquia visual
- animações suaves
- feedback visual
- estados vazios bonitos
- loading states
- skeletons
- mensagens de erro claras
- confirmações antes de ações destrutivas

---



# Responsividade

Desktop:

```text
Sidebar + Dashboard
```

Tablet:

```text
Sidebar compacta
```

Mobile:

```text
Bottom Navigation
```

A experiência mobile não deve simplesmente ser uma versão espremida da interface desktop.

---



# Qualidade do código

Quero:

- TypeScript strict
- componentes reutilizáveis
- código modular
- funções pequenas
- tipagem forte
- validação de dados
- tratamento de erros
- API documentada
- testes básicos
- migrations do banco
- `.env.example`
- Docker Compose
- README completo

Não colocar tudo em um único arquivo.

Evitar:

```text
components gigantes
```

e:

```text
lógica de negócio dentro dos componentes React
```

---



# Importante

Antes de começar a implementar:

1. Estruture a arquitetura.
2. Crie o banco de dados.
3. Crie os modelos.
4. Crie a API.
5. Crie o sistema de autenticação.
6. Crie o design system.
7. Crie o layout principal.
8. Implemente o Dashboard.
9. Implemente as funcionalidades financeiras progressivamente.
10. Teste cada módulo.

**Não tente criar todas as funcionalidades em um único componente ou arquivo.**

Priorize uma base sólida e extensível.

O resultado final deve parecer um **produto real**, não um projeto acadêmico ou um CRUD genérico.

A referência estética principal é:

[Figma — macOS 27 UI Kit](https://www.figma.com/pt-br/comunidade/file/1651309434229735362/macos-27?utm_source=chatgpt.com)

Use o screenshot fornecido como referência adicional para o estilo visual.

**Comece criando a arquitetura e o design system antes de implementar todas as páginas.**