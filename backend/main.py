"""Ponto de entrada de linha de comando do backend.

    python main.py runserver     sobe a API (aplica as migrations antes)
    python main.py migrate       aplica as migrations e sai
    python main.py check         testa a conexao com o banco e o Supabase
    python main.py routes        lista as rotas registradas

A aplicacao em si vive em `app/main.py`; este arquivo so existe para dar um
comando curto e previsivel.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))


def _run_migrations() -> None:
    from alembic import command
    from alembic.config import Config

    config = Config(str(BASE_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BASE_DIR / "alembic"))
    command.upgrade(config, "head")


def runserver(args: argparse.Namespace) -> int:
    import uvicorn

    from app.core.config import settings

    if not args.skip_migrations:
        print("Aplicando migrations...")
        try:
            _run_migrations()
        except Exception as exc:  # noqa: BLE001 - a mensagem importa mais que o tipo
            print(f"\nFalha ao aplicar as migrations: {exc}")
            print("Suba mesmo assim com: python main.py runserver --skip-migrations")
            return 1

    print(f"\n  API      http://{args.host}:{args.port}")
    print(f"  Docs     http://{args.host}:{args.port}/docs")
    print(f"  Ambiente {settings.environment}\n")

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level,
    )
    return 0


def migrate(_: argparse.Namespace) -> int:
    _run_migrations()
    print("Migrations aplicadas.")
    return 0


def check(_: argparse.Namespace) -> int:
    """Confere as duas dependencias externas antes de acusar erro no codigo."""
    import httpx
    from sqlalchemy import text

    from app.core.config import settings

    ok = True

    print("Banco de dados")
    try:
        from app.database.session import engine

        with engine.connect() as connection:
            version = connection.execute(text("select version()")).scalar_one()
            tables = connection.execute(
                text(
                    "select count(*) from information_schema.tables "
                    "where table_schema = 'public'"
                )
            ).scalar_one()
        print(f"  ok       {version.split(',')[0]}")
        print(f"  tabelas  {tables} no schema public")
    except Exception as exc:  # noqa: BLE001
        ok = False
        print(f"  FALHOU   {exc}")

    print("\nSupabase Auth")
    if not settings.supabase_url:
        ok = False
        print("  FALHOU   SUPABASE_URL nao configurada")
    else:
        try:
            response = httpx.get(settings.jwks_url, timeout=15)
            response.raise_for_status()
            keys = response.json().get("keys", [])
            algorithms = ", ".join(sorted({key.get("alg", "?") for key in keys}))
            print(f"  ok       JWKS respondeu com {len(keys)} chave(s) [{algorithms}]")
        except Exception as exc:  # noqa: BLE001
            ok = False
            print(f"  FALHOU   {exc}")

    print("\nTudo certo." if ok else "\nHa problemas acima.")
    return 0 if ok else 1


def routes(_: argparse.Namespace) -> int:
    from app.main import app

    for route in sorted(app.routes, key=lambda item: getattr(item, "path", "")):
        methods = getattr(route, "methods", None)
        path = getattr(route, "path", "")
        if methods and path:
            print(f"  {','.join(sorted(methods - {'HEAD', 'OPTIONS'})):<18} {path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python main.py", description=__doc__)
    subparsers = parser.add_subparsers(dest="command")

    server = subparsers.add_parser("runserver", help="Sobe a API")
    server.add_argument("--host", default="127.0.0.1")
    server.add_argument("--port", type=int, default=8000)
    server.add_argument(
        "--no-reload", dest="reload", action="store_false", help="Desliga o auto-reload"
    )
    server.add_argument(
        "--skip-migrations",
        action="store_true",
        help="Nao aplica as migrations antes de subir",
    )
    server.add_argument("--log-level", default="info")
    server.set_defaults(func=runserver, reload=True)

    subparsers.add_parser("migrate", help="Aplica as migrations").set_defaults(func=migrate)
    subparsers.add_parser("check", help="Testa banco e Supabase").set_defaults(func=check)
    subparsers.add_parser("routes", help="Lista as rotas").set_defaults(func=routes)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not getattr(args, "func", None):
        parser.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
