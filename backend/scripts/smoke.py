"""Teste de fumaca ponta a ponta contra a API rodando.

Autentica no Supabase, exercita todos os modulos e imprime o resultado. Nao
substitui a suite de testes: serve para conferir rapidamente que o ambiente
(banco, auth, rede) esta de pe.

    python scripts/smoke.py
"""
from __future__ import annotations

import os
import sys
from datetime import date, timedelta

import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings  # noqa: E402

API = os.environ.get("SMOKE_API_URL", "http://127.0.0.1:8000/api/v1")
EMAIL = os.environ.get("SMOKE_EMAIL", "teste.fin@example.com")
PASSWORD = os.environ.get("SMOKE_PASSWORD", "SenhaDeTeste!2026")

ok_count = 0
fail_count = 0


def check(label: str, condition: bool, detail: str = "") -> None:
    global ok_count, fail_count
    if condition:
        ok_count += 1
        print(f"  ok    {label}" + (f"  ({detail})" if detail else ""))
    else:
        fail_count += 1
        print(f"  FALHA {label}" + (f"  ({detail})" if detail else ""))


def login() -> str:
    response = httpx.post(
        f"{settings.supabase_url}/auth/v1/token?grant_type=password",
        headers={"apikey": settings.supabase_anon_key},
        json={"email": EMAIL, "password": PASSWORD},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def main() -> int:
    token = login()
    client = httpx.Client(
        base_url=API, headers={"Authorization": f"Bearer {token}"}, timeout=60
    )
    today = date.today()

    print("\nPerfil e categorias")
    me = client.get("/users/me").json()
    check("perfil carregado", "id" in me, me.get("email", ""))
    categories = client.get("/categories").json()
    check("categorias semeadas", len(categories) >= 12, f"{len(categories)} categorias")
    by_name = {item["name"]: item for item in categories}

    print("\nContas")
    account = client.post(
        "/accounts",
        json={"name": "Conta Corrente", "bank": "Itau", "type": "checking",
              "initial_balance": "1000.00", "color": "#5E7CE2"},
    ).json()
    check("conta criada", "id" in account, account.get("name", ""))
    savings = client.post(
        "/accounts", json={"name": "Poupanca", "type": "savings", "initial_balance": "500.00"}
    ).json()

    print("\nCartoes")
    card = client.post(
        "/cards",
        json={"name": "Cartao Itau", "bank": "Itau", "brand": "visa",
              "limit_amount": "2500.00", "closing_day": 3, "due_day": 10,
              "account_id": account["id"]},
    ).json()
    check("cartao criado", "id" in card, card.get("name", ""))
    check("fatura calculada", card["current_invoice"] is not None,
          f"vence {card['current_invoice']['due_date']}")

    print("\nTransacoes")
    salary = client.post(
        "/transactions",
        json={"type": "income", "amount": "4500.00", "description": "Salario",
              "date": str(today.replace(day=5)), "account_id": account["id"],
              "category_id": by_name["Salário"]["id"]},
    ).json()
    check("receita lancada", len(salary) == 1)

    client.post(
        "/transactions",
        json={"type": "expense", "amount": "620.00", "description": "Mercado",
              "date": str(today), "account_id": account["id"],
              "category_id": by_name["Alimentação"]["id"]},
    )
    transfer = client.post(
        "/transactions",
        json={"type": "transfer", "amount": "200.00", "description": "Para a poupanca",
              "date": str(today), "account_id": account["id"],
              "transfer_account_id": savings["id"]},
    )
    check("transferencia aceita", transfer.status_code == 201)

    invalid = client.post(
        "/transactions",
        json={"type": "transfer", "amount": "10.00", "description": "Invalida",
              "date": str(today), "account_id": account["id"],
              "transfer_account_id": account["id"]},
    )
    check("transferencia para a mesma conta rejeitada", invalid.status_code == 422)

    print("\nSaldos")
    accounts = client.get("/accounts").json()
    balances = {item["name"]: item["current_balance"] for item in accounts["accounts"]}
    # 1000 + 4500 - 620 - 200 = 4680
    check("saldo da conta corrente", balances["Conta Corrente"] == "4680.00",
          balances["Conta Corrente"])
    # 500 + 200 = 700
    check("saldo da poupanca", balances["Poupanca"] == "700.00", balances["Poupanca"])

    print("\nParcelamento")
    parcels = client.post(
        "/transactions",
        json={"type": "expense", "amount": "4200.00", "description": "Notebook",
              "date": str(today), "card_id": card["id"], "installments": 12,
              "category_id": by_name["Compras"]["id"]},
    ).json()
    check("12 parcelas geradas", len(parcels) == 12)
    check("parcela de 350,00", parcels[0]["amount"] == "350.00", parcels[0]["amount"])
    plans = client.get("/installments").json()
    check("plano listado", len(plans) == 1,
          f"{plans[0]['paid_installments']}/{plans[0]['installments_count']}")

    print("\nLimite do cartao")
    card = client.get(f"/cards/{card['id']}").json()
    check("limite consumido", card["used_limit"] != "0.00", card["used_limit"])
    # A compra parcelada (4200) passa do limite (2500) de proposito: o app
    # registra o que o usuario informou e mostra disponivel zerado, em vez de
    # recusar o lancamento.
    expected_available = max(
        float(card["limit_amount"]) - float(card["used_limit"]), 0.0
    )
    check("limite disponivel nunca negativo",
          float(card["available_limit"]) == expected_available,
          f"disponivel {card['available_limit']}")

    print("\nFiltros e ordenacao")
    page = client.get("/transactions", params={"type": "expense", "page_size": 5}).json()
    check("paginacao", page["page_size"] == 5 and page["total"] >= 13, f"total {page['total']}")
    search = client.get("/transactions", params={"search": "Notebook"}).json()
    check("busca textual", search["total"] == 12, f"{search['total']} resultados")
    sorted_page = client.get(
        "/transactions", params={"sort_by": "amount", "sort_order": "desc", "page_size": 1}
    ).json()
    check("ordenacao por valor", sorted_page["items"][0]["amount"] == "4500.00")

    print("\nContas recorrentes")
    rule = client.post(
        "/recurring",
        json={"description": "Aluguel", "amount": "1200.00", "type": "expense",
              "frequency": "monthly", "day_of_month": 5, "start_date": str(today.replace(day=1)),
              "account_id": account["id"], "category_id": by_name["Moradia"]["id"]},
    ).json()
    check("regra criada", "id" in rule)
    occurrences = client.get(
        "/recurring/occurrences",
        params={"date_from": str(today), "date_to": str(today + timedelta(days=120))},
    ).json()
    check("ocorrencias previstas", len(occurrences) >= 3, f"{len(occurrences)} ocorrencias")

    print("\nOrcamento")
    client.put(
        "/budgets",
        json={"month": str(today), "category_id": by_name["Alimentação"]["id"], "amount": "700.00"},
    )
    budget = client.get("/budgets", params={"month": str(today)}).json()
    item = budget["items"][0]
    check("orcamento com realizado", item["spent"] == "620.00", f"gasto {item['spent']}")
    check("percentual usado", item["used_percentage"] == "88.57", item["used_percentage"])

    print("\nMetas")
    goal = client.post(
        "/goals",
        json={"name": "Reserva de emergencia", "target_amount": "10000.00",
              "current_amount": "3200.00"},
    ).json()
    check("progresso da meta", goal["progress"] == "32.00", f"{goal['progress']}%")
    goal = client.post(f"/goals/{goal['id']}/contributions", json={"amount": "800.00"}).json()
    check("aporte somado", goal["current_amount"] == "4000.00", goal["current_amount"])

    print("\nInvestimentos")
    client.post(
        "/investments",
        json={"asset": "PETR4", "type": "stock", "quantity": "100",
              "average_price": "30.00", "current_price": "36.00", "institution": "XP"},
    )
    portfolio = client.get("/investments").json()
    check("valor da carteira", portfolio["current_value"] == "3600.00", portfolio["current_value"])
    check("rentabilidade", portfolio["profitability"] == "20.00", f"{portfolio['profitability']}%")

    print("\nDashboard e relatorios")
    dashboard = client.get("/reports/dashboard", params={"period": "30d"}).json()
    overview = dashboard["overview"]
    check("receitas do mes", overview["income"] == "4500.00", overview["income"])
    check("patrimonio calculado", overview["net_worth"] is not None, overview["net_worth"])
    check("serie de fluxo", len(dashboard["cash_flow"]["points"]) == 30,
          f"{len(dashboard['cash_flow']['points'])} pontos")
    check("gastos por categoria", len(dashboard["expenses_by_category"]["items"]) >= 1)
    check("proximas contas", isinstance(dashboard["upcoming_bills"], list),
          f"{len(dashboard['upcoming_bills'])} contas")

    yearly = client.get("/reports/cash-flow", params={"period": "1y"}).json()
    check("periodo anual agrupa por mes", yearly["granularity"] == "month")
    check("relatorio mensal", len(client.get("/reports/monthly").json()["points"]) == 12)
    check("evolucao do patrimonio", len(client.get("/reports/net-worth").json()["points"]) == 12)
    check("gastos por cartao", client.get("/reports/card-spending").json()["total"] != "0.00")
    check("resumo de recorrentes", "recurring_expenses" in client.get("/reports/recurring").json())

    print("\nRegras de protecao")
    conflict = client.delete(f"/accounts/{account['id']}")
    check("conta com movimento nao e excluida", conflict.status_code == 409)
    system_category = client.delete(f"/categories/{by_name['Moradia']['id']}")
    check("categoria padrao nao e excluida", system_category.status_code == 409)
    missing = client.get("/accounts/00000000-0000-0000-0000-000000000000")
    check("recurso inexistente devolve 404", missing.status_code == 404)

    client.close()
    print(f"\n{ok_count} verificacoes ok, {fail_count} falhas")
    return 1 if fail_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
