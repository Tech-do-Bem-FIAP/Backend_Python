"""
database.py — Camada de conexão com o Oracle Database (FIAP).

Centraliza a configuração de credenciais e expõe um context manager
para obter conexões e cursores com tratamento adequado de exceções.

Requer o pacote `oracledb` (substituto moderno do cx_Oracle):
    pip install oracledb
"""

from __future__ import annotations

from contextlib import contextmanager

try:
    import oracledb
except ImportError as exc:
    raise ImportError(
        "O pacote 'oracledb' não está instalado.\n"
        "Execute: pip install oracledb"
    ) from exc


# ── Configuração de conexão (FIAP) ────────────────────────

HOST = "oracle.fiap.com.br"
PORT = 1521
SID = "orcl"
USUARIO = "RM567010"
SENHA = "160494"

# DSN no formato Easy Connect, usando SID (compatível com a string JDBC):
#   jdbc:oracle:thin:@oracle.fiap.com.br:1521:orcl
DSN = oracledb.makedsn(HOST, PORT, sid=SID)


# ── Conexão ───────────────────────────────────────────────

def conectar() -> "oracledb.Connection":
    """Abre uma conexão com o banco. Lança oracledb.DatabaseError em caso de falha."""
    return oracledb.connect(user=USUARIO, password=SENHA, dsn=DSN)


@contextmanager
def cursor():
    """
    Context manager: abre conexão + cursor, faz commit automático
    em caso de sucesso e rollback em caso de erro.

    Uso:
        with database.cursor() as cur:
            cur.execute("SELECT ...")
            linhas = cur.fetchall()
    """
    conexao = conectar()
    cur = conexao.cursor()
    try:
        yield cur
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        cur.close()
        conexao.close()


def testar_conexao() -> bool:
    """Retorna True se conseguir abrir a conexão; imprime o erro se falhar."""
    try:
        with cursor() as cur:
            cur.execute("SELECT 1 FROM DUAL")
            cur.fetchone()
        return True
    except oracledb.DatabaseError as exc:
        print(f"  [ERRO] Falha ao conectar no Oracle: {exc}")
        return False
