"""
storage.py — Persistência sobre Oracle Database.

Mantém a API histórica do projeto:
    carregar(entidade)   -> list[dict]
    salvar(entidade, dados)
    proximo_id(lista)    -> int
    inicializar()        -> testa a conexão

Internamente, cada entidade é mapeada para uma tabela em SCHEMAS. As
listas devolvidas por carregar() são dicts com as mesmas chaves usadas
na versão JSON da Sprint 3 — assim crud.py e os painéis não precisam
mudar.

Estratégia do salvar(): faz diff entre a lista informada e o estado
atual do banco, aplicando INSERT/UPDATE/DELETE conforme necessário.
Isso preserva o padrão "carrega tudo, modifica em memória, salva tudo"
da Sprint 3 sem precisar reescrever a lógica das telas.
"""

from __future__ import annotations

import json
from typing import Any

import oracledb

from modules import database


# ── Definição das entidades / tabelas ─────────────────────

SCHEMAS: dict[str, dict[str, Any]] = {
    "colaboradores": {
        "table": "tdb_colaboradores",
        "cols": ["id", "nome", "cpf", "email", "senha", "cargo", "disponibilidade"],
        "json_cols": [],
    },
    "dentistas": {
        "table": "tdb_dentistas",
        "cols": ["id", "nome", "cpf", "email", "senha", "cro", "especialidade",
                 "disponibilidade", "id_colaborador"],
        "json_cols": [],
    },
    "pacientes": {
        "table": "tdb_pacientes",
        "cols": ["id", "nome", "cpf", "data_nasc", "telefone", "email", "id_dentista",
                 "cep", "logradouro", "bairro", "cidade", "uf"],
        "json_cols": [],
    },
    "campanhas": {
        "table": "tdb_campanhas",
        "cols": ["id", "nome", "local", "data_inicio", "data_fim", "id_colaborador"],
        "json_cols": [],
    },
    "atendimentos": {
        "table": "tdb_atendimentos",
        "cols": ["id", "id_paciente", "id_dentista", "id_campanha", "data",
                 "tipo", "status", "observacoes", "exames"],
        "json_cols": ["exames"],
    },
    "notificacoes": {
        "table": "tdb_notificacoes",
        "cols": ["id", "mensagem", "data_envio", "status_envio", "canal",
                 "id_colaborador", "id_dentista"],
        "json_cols": [],
    },
    "anotacoes": {
        "table": "tdb_anotacoes",
        "cols": ["id", "texto", "data", "autor_id", "autor_tipo", "sobre_id", "sobre_tipo"],
        "json_cols": [],
    },
    "solicitacoes": {
        "table": "tdb_solicitacoes",
        "cols": ["id", "tipo", "dados", "status", "data"],
        "json_cols": ["dados"],
    },
}


# ── Inicialização ─────────────────────────────────────────

def inicializar() -> None:
    """Testa a conexão com o banco. Não cria tabelas (use Oracle_Scripts.sql)."""
    if not database.testar_conexao():
        raise RuntimeError(
            "Não foi possível conectar ao Oracle. Verifique a rede / VPN da FIAP "
            "e os scripts em Oracle_Scripts.sql."
        )


# ── Conversões dict <-> linha ─────────────────────────────

def _to_db(coluna: str, valor: Any, schema: dict) -> Any:
    """Converte um valor Python para o formato esperado pelo bind do oracledb."""
    if valor is None:
        return None
    if coluna in schema["json_cols"]:
        return json.dumps(valor, ensure_ascii=False)
    return valor


def _from_db(coluna: str, valor: Any, schema: dict) -> Any:
    """Converte um valor vindo do oracledb para Python (desserializa JSON).
    As colunas JSON são VARCHAR2 — voltam como str e são convertidas
    de volta para list/dict com json.loads()."""
    if valor is None:
        return None
    if coluna in schema["json_cols"]:
        try:
            return json.loads(valor) if valor else None
        except (ValueError, TypeError):
            return None
    return valor


def _linha_para_dict(linha: tuple, schema: dict) -> dict:
    """Converte uma tupla retornada pelo cursor em dict {coluna: valor}."""
    return {c: _from_db(c, v, schema) for c, v in zip(schema["cols"], linha)}


# ── Leitura ───────────────────────────────────────────────

def carregar(entidade: str) -> list[dict]:
    """Lê todos os registros de uma entidade e devolve uma lista de dicts."""
    schema = SCHEMAS[entidade]
    cols_sql = ", ".join(schema["cols"])
    sql = f"SELECT {cols_sql} FROM {schema['table']} ORDER BY id"
    try:
        with database.cursor() as cur:
            cur.execute(sql)
            linhas = cur.fetchall()
    except oracledb.DatabaseError as exc:
        print(f"  [ERRO] Falha ao ler '{entidade}': {exc}")
        raise
    return [_linha_para_dict(l, schema) for l in linhas]


# ── Escrita (sync entre lista e tabela) ───────────────────

def salvar(entidade: str, dados: list[dict]) -> None:
    """
    Sincroniza a tabela com a lista informada:
      - registros cujo id não existe no banco -> INSERT
      - registros cujo id já existe           -> UPDATE
      - linhas no banco cujo id sumiu da lista -> DELETE
    """
    schema = SCHEMAS[entidade]
    tabela = schema["table"]
    cols = schema["cols"]
    cols_sem_id = [c for c in cols if c != "id"]

    sql_select_ids = f"SELECT id FROM {tabela}"
    sql_insert = (
        f"INSERT INTO {tabela} ({', '.join(cols)}) "
        f"VALUES ({', '.join(':' + c for c in cols)})"
    )
    sql_update = (
        f"UPDATE {tabela} SET "
        f"{', '.join(f'{c} = :{c}' for c in cols_sem_id)} "
        f"WHERE id = :id"
    )
    sql_delete = f"DELETE FROM {tabela} WHERE id = :id"

    try:
        with database.cursor() as cur:
            cur.execute(sql_select_ids)
            ids_existentes = {linha[0] for linha in cur.fetchall()}
            ids_novos = {item["id"] for item in dados}

            # DELETE: ids removidos da lista
            for id_removido in ids_existentes - ids_novos:
                cur.execute(sql_delete, {"id": id_removido})

            # INSERT / UPDATE
            for item in dados:
                binds = {c: _to_db(c, item.get(c), schema) for c in cols}
                if item["id"] in ids_existentes:
                    cur.execute(sql_update, binds)
                else:
                    cur.execute(sql_insert, binds)
    except oracledb.DatabaseError as exc:
        print(f"  [ERRO] Falha ao salvar '{entidade}': {exc}")
        raise


# ── Geração de IDs (mantida por compatibilidade) ──────────

def proximo_id(lista: list) -> int:
    """Retorna o próximo id baseado na lista em memória. Sequências do Oracle
    permanecem definidas no schema, mas o app continua controlando os ids."""
    if not lista:
        return 1
    return max(item["id"] for item in lista) + 1
