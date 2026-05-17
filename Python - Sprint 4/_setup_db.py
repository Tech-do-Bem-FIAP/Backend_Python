"""
Executa Oracle_Scripts.sql contra o banco da FIAP.

Pode ser rodado uma única vez para criar/recriar todas as tabelas e
sequências do projeto. Use:
    .venv/bin/python _setup_db.py
"""

from __future__ import annotations

import os
import sys

import oracledb

from modules import database

CAMINHO_SQL = os.path.join(os.path.dirname(__file__), "Oracle_Scripts.sql")


def parse_script(conteudo: str) -> list[str]:
    """Divide o script em statements executáveis.
    PL/SQL blocks são terminados por uma linha contendo apenas '/'.
    Statements DDL/DML normais são terminados por ';' no fim da linha."""
    statements: list[str] = []
    buffer: list[str] = []
    in_plsql = False

    for raw in conteudo.splitlines():
        stripped = raw.strip()

        # Marca início de bloco PL/SQL
        if stripped.upper().startswith("BEGIN "):
            in_plsql = True

        # Fim de bloco PL/SQL: linha com apenas "/"
        if in_plsql and stripped == "/":
            stmt = "\n".join(buffer).strip()
            if stmt:
                statements.append(stmt)
            buffer = []
            in_plsql = False
            continue

        # Ignora comentários e linhas em branco fora de statements
        if not stripped or stripped.startswith("--"):
            if buffer:
                buffer.append(raw)
            continue

        buffer.append(raw)

        # Fim de statement DDL/DML normal
        if not in_plsql and stripped.endswith(";"):
            stmt = "\n".join(buffer).strip().rstrip(";").strip()
            if stmt:
                statements.append(stmt)
            buffer = []

    return statements


def main() -> int:
    if not os.path.exists(CAMINHO_SQL):
        print(f"[ERRO] Não encontrei {CAMINHO_SQL}")
        return 1

    with open(CAMINHO_SQL, "r", encoding="utf-8") as arquivo:
        conteudo = arquivo.read()

    statements = parse_script(conteudo)
    print(f"Parsed {len(statements)} statements de {CAMINHO_SQL}\n")

    try:
        conexao = database.conectar()
    except oracledb.DatabaseError as exc:
        print(f"[FATAL] Não consegui conectar: {exc}")
        return 1

    cur = conexao.cursor()
    sucesso = 0
    falhou = 0
    try:
        for i, stmt in enumerate(statements, 1):
            primeira_linha = stmt.splitlines()[0][:80]
            try:
                cur.execute(stmt)
                print(f"  [{i:02d}] OK     {primeira_linha}")
                sucesso += 1
            except oracledb.DatabaseError as exc:
                print(f"  [{i:02d}] FALHA  {primeira_linha}")
                print(f"       └─ {exc}")
                falhou += 1
        conexao.commit()
    finally:
        cur.close()
        conexao.close()

    print(f"\nResumo: {sucesso} sucesso(s), {falhou} falha(s).")
    return 0 if falhou == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
