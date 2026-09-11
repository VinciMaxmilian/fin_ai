"""Categorias criadas automaticamente para cada novo usuario.

As cores saem da paleta categorica validada em `frontend/src/components/charts/
palette.ts`: oito matizes que passam nos testes de separacao para daltonismo e
de contraste, nos temas claro e escuro.

A paleta tem oito posicoes e ha nove categorias de despesa, entao duas duplas
compartilham matiz (Transporte/Viagens e Educacao/Assinaturas). Isso e aceitavel
porque todo grafico de categoria no app e uma lista de barras ordenada com nome e
valor escritos em cada linha: a cor reforca a identidade, nao a carrega sozinha.
Gerar uma nona cor deixaria a paleta abaixo do piso de croma e faria duas
categorias virarem cinza indistinto.
"""
from __future__ import annotations

from app.categories.models import CategoryKind

# Posicoes da paleta categorica (tema claro).
BLUE = "#2A78D6"
ORANGE = "#EB6834"
AQUA = "#1BAF7A"
YELLOW = "#EDA100"
MAGENTA = "#E87BA4"
GREEN = "#008300"
VIOLET = "#4A3AA7"
RED = "#E34948"
# Reservado para o agrupamento "Outros" nos graficos.
MUTED = "#898781"

DEFAULT_CATEGORIES: list[dict[str, str | CategoryKind]] = [
    {"name": "Moradia", "kind": CategoryKind.expense, "color": BLUE, "icon": "home"},
    {"name": "Alimentação", "kind": CategoryKind.expense, "color": ORANGE, "icon": "utensils"},
    {"name": "Transporte", "kind": CategoryKind.expense, "color": AQUA, "icon": "car"},
    {"name": "Compras", "kind": CategoryKind.expense, "color": YELLOW, "icon": "bag"},
    {"name": "Lazer", "kind": CategoryKind.expense, "color": MAGENTA, "icon": "sparkles"},
    {"name": "Educação", "kind": CategoryKind.expense, "color": VIOLET, "icon": "book"},
    {"name": "Saúde", "kind": CategoryKind.expense, "color": RED, "icon": "heart"},
    {"name": "Assinaturas", "kind": CategoryKind.expense, "color": VIOLET, "icon": "repeat"},
    {"name": "Viagens", "kind": CategoryKind.expense, "color": AQUA, "icon": "plane"},
    {"name": "Investimentos", "kind": CategoryKind.both, "color": GREEN, "icon": "trending-up"},
    {"name": "Salário", "kind": CategoryKind.income, "color": GREEN, "icon": "wallet"},
    {"name": "Outros", "kind": CategoryKind.both, "color": MUTED, "icon": "tag"},
]
