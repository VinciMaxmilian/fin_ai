"""Copia o banco para outro projeto do Supabase (tipicamente outra regiao).

Motivo: a latencia ate o banco multiplica cada consulta. Medido daqui:

    us-west-2 (Oregon)      190 ms
    sa-east-1 (Sao Paulo)    11 ms

Com ~10 consultas por pagina, isso e a diferenca entre 2 s e 0,3 s.

    python scripts/migrar_regiao.py --destino "postgresql+psycopg2://..." [--executar]

Sem `--executar` o script apenas mostra o que faria.

O que e copiado:

  auth.users, auth.identities   para os logins continuarem valendo (a senha
                                criptografada vive em auth.users; sem isso todo
                                mundo teria de se cadastrar de novo)
  public.*                      os dados do aplicativo, na ordem das chaves
                                estrangeiras

O que NAO e copiado: sessoes e refresh tokens. Todo mundo faz login de novo uma
vez -- o que e desejavel, porque os tokens antigos foram emitidos por outro
projeto e nao seriam validos no novo mesmo.

ANTES DE RODAR
--------------
1. Crie o projeto novo no painel do Supabase, na regiao desejada.
2. Anote a connection string do **Session Pooler** (o host direto costuma ser
   so IPv6 e nao e alcancavel de toda rede).
3. Rode este script. Ele aplica as migrations no destino antes de copiar.
4. Troque as variaveis no `.env` e reinicie a API.

O banco de origem nao e modificado em momento algum.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.core.config import settings  # noqa: E402

# Ordem das chaves estrangeiras: uma tabela so entra depois daquelas de que
# depende. Inverter isso quebra a copia.
TABELAS_PUBLIC = [
    "app_user",
    "account",
    "card",
    "category",
    "installment_plan",
    "recurring_rule",
    "transaction",
    "budget",
    "goal",
    "investment",
]

# Identidade: o suficiente para senha e OAuth continuarem funcionando.
TABELAS_AUTH = ["users", "identities"]


def contar(engine: Engine, schema: str, tabela: str) -> int:
    with engine.connect() as conn:
        return conn.execute(text(f"select count(*) from {schema}.{tabela}")).scalar_one()


def colunas_comuns(origem: Engine, destino: Engine, schema: str, tabela: str) -> list[str]:
    """Colunas presentes nos dois lados.

    Versoes diferentes do GoTrue podem ter colunas distintas em auth.users;
    copiar so a intersecao evita quebrar por causa de uma coluna nova.
    """
    consulta = text(
        "select column_name from information_schema.columns "
        "where table_schema = :s and table_name = :t"
    )
    with origem.connect() as conn:
        a = {r[0] for r in conn.execute(consulta, {"s": schema, "t": tabela})}
    with destino.connect() as conn:
        b = {r[0] for r in conn.execute(consulta, {"s": schema, "t": tabela})}
    return sorted(a & b)


def copiar(origem: Engine, destino: Engine, schema: str, tabela: str, executar: bool) -> int:
    colunas = colunas_comuns(origem, destino, schema, tabela)
    if not colunas:
        print(f"    {schema}.{tabela}: sem colunas em comum, pulando")
        return 0

    with origem.connect() as conn:
        linhas = conn.execute(
            text(f"select {', '.join(colunas)} from {schema}.{tabela}")
        ).mappings().all()

    if not linhas:
        print(f"    {schema}.{tabela}: vazia")
        return 0

    if not executar:
        print(f"    {schema}.{tabela}: {len(linhas)} linhas (simulacao)")
        return len(linhas)

    alvo = ", ".join(colunas)
    valores = ", ".join(f":{c}" for c in colunas)
    # ON CONFLICT DO NOTHING torna a copia reexecutavel sem duplicar.
    comando = text(
        f"insert into {schema}.{tabela} ({alvo}) values ({valores}) "
        "on conflict do nothing"
    )
    with destino.begin() as conn:
        conn.execute(comando, [dict(linha) for linha in linhas])

    print(f"    {schema}.{tabela}: {len(linhas)} linhas copiadas")
    return len(linhas)


def aplicar_migrations(url: str) -> None:
    from alembic import command
    from alembic.config import Config

    config = Config(str(BASE_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BASE_DIR / "alembic"))
    config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    command.upgrade(config, "head")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--destino",
        default=os.environ.get("DESTINO_DATABASE_URL", ""),
        help="URL SQLAlchemy do banco de destino (ou DESTINO_DATABASE_URL no ambiente)",
    )
    parser.add_argument(
        "--executar",
        action="store_true",
        help="Escreve de verdade. Sem isso, apenas simula.",
    )
    parser.add_argument(
        "--forcar",
        action="store_true",
        help="Copia mesmo que o destino ja tenha dados.",
    )
    args = parser.parse_args()

    if not args.destino:
        print("Informe --destino com a URL do banco novo.")
        return 1

    conexao = {"sslmode": "require", "connect_timeout": 20}
    origem = create_engine(settings.sqlalchemy_url, connect_args=conexao)
    destino = create_engine(args.destino, connect_args=conexao)

    print("Origem :", settings.postgres_host)
    print("Destino:", args.destino.split("@")[-1].split("/")[0])
    print("Modo   :", "EXECUCAO REAL" if args.executar else "simulacao\n")

    print("\nAplicando migrations no destino...")
    if args.executar:
        aplicar_migrations(args.destino)
        print("  ok")
    else:
        print("  (simulacao: nao aplicadas)")
        # Sem as tabelas no destino, a simulacao nao consegue comparar colunas.
        try:
            contar(destino, "public", "app_user")
        except Exception:
            print("\n  O destino ainda nao tem as tabelas. Rode com --executar")
            print("  para aplicar as migrations e copiar.")
            return 0

    if not args.forcar:
        existentes = sum(contar(destino, "public", t) for t in TABELAS_PUBLIC)
        if existentes:
            print(f"\nO destino ja tem {existentes} linhas em public.")
            print("Use --forcar se quiser copiar mesmo assim (nao duplica: usa ON CONFLICT).")
            return 1

    print("\nIdentidade (auth):")
    for tabela in TABELAS_AUTH:
        copiar(origem, destino, "auth", tabela, args.executar)

    print("\nDados do aplicativo (public):")
    total = 0
    for tabela in TABELAS_PUBLIC:
        total += copiar(origem, destino, "public", tabela, args.executar)

    if args.executar:
        print("\nConferindo:")
        divergencias = 0
        for tabela in TABELAS_PUBLIC:
            a, b = contar(origem, "public", tabela), contar(destino, "public", tabela)
            marca = "ok " if a == b else "!! "
            if a != b:
                divergencias += 1
            print(f"  {marca}{tabela:18} origem {a:5}  destino {b:5}")

        if divergencias:
            print(f"\n{divergencias} tabela(s) com contagem diferente. Investigue antes de trocar o .env.")
            return 1

        print(f"\n{total} linhas copiadas. Proximos passos:")
        print("  1. Atualize POSTGRES_* e SUPABASE_* no .env para o projeto novo")
        print("  2. Reaplique a blindagem: as migrations ja incluem RLS e REVOKE")
        print("  3. Reinicie a API e rode: python main.py check")
    else:
        print(f"\n{total} linhas seriam copiadas. Rode de novo com --executar.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
