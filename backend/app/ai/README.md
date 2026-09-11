# Camada de IA (reservada)

Nada aqui está implementado. A pasta existe para marcar onde a IA entra quando
for a hora, mantendo os módulos financeiros intocados.

```
FastAPI
  ├── accounts, cards, transactions, ...   (regra de negócio)
  ├── reports                              (agregações)
  └── ai/                                  ← provedores + ferramentas
        ├── provider.py   contrato AIProvider
        └── providers/    Gemini, OpenAI, LLM local, ...
```

As ferramentas expostas à IA (`get_transactions`, `get_balance`,
`create_transaction`, `generate_report`, …) devem chamar os serviços existentes
de cada módulo. Nenhuma delas deve montar SQL própria — isso duplicaria a regra
de negócio e abriria caminho para vazar dado entre usuários.
