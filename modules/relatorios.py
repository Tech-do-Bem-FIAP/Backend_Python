"""
relatorios.py — Consultas filtradas (SELECT/WHERE) com exportação para JSON.

Implementa o requisito da Sprint 4:
    "Realizar ao menos duas consultas no banco de dados utilizando
     filtros (utilizar select/where) e disponibilizar uma opção para
     exportar os dados dessas consultas para um arquivo JSON."

Cada relatório:
  1. Pergunta os filtros ao usuário.
  2. Executa uma SELECT com WHERE no Oracle (binds parametrizados).
  3. Exibe o resultado em tabela.
  4. Oferece a opção de exportar o resultado como .json.
"""

from __future__ import annotations

import json
import os
from datetime import datetime

import oracledb

from modules import database, utils
from modules.auth import tem_permissao

PASTA_EXPORT = "exports"


# ── Menu principal ────────────────────────────────────────

def menu_relatorios(usuario_logado: dict) -> None:
    if not tem_permissao(usuario_logado, 2):
        print("  Acesso negado. Necessário cargo Auxiliar ou superior.")
        utils.pausar()
        return

    while True:
        utils.cabecalho("RELATÓRIOS")
        print("  [1] Pacientes por dentista")
        print("  [2] Atendimentos por status e período")
        print("  [3] Notificações enviadas a partir de uma data")
        print("  [0] Voltar")
        opcao = utils.input_inteiro("  Opção: ", 0, 3)

        try:
            if opcao == 0:
                break
            elif opcao == 1:
                relatorio_pacientes_por_dentista()
            elif opcao == 2:
                relatorio_atendimentos_por_status_periodo()
            elif opcao == 3:
                relatorio_notificacoes_a_partir_de()
        except oracledb.DatabaseError as exc:
            print(f"\n  [ERRO] Falha ao executar relatório: {exc}")
            utils.pausar()


# ── Relatório 1: Pacientes por dentista ───────────────────

def relatorio_pacientes_por_dentista() -> None:
    """SELECT/WHERE filtrando por id_dentista (e opcionalmente por UF)."""
    utils.cabecalho("RELATÓRIO — PACIENTES POR DENTISTA")

    # Lista dentistas para o usuário escolher
    with database.cursor() as cur:
        cur.execute("SELECT id, nome, cro FROM tdb_dentistas ORDER BY nome")
        dentistas = cur.fetchall()

    if not dentistas:
        print("  Nenhum dentista cadastrado.")
        utils.pausar()
        return

    for did, nome, cro in dentistas:
        print(f"  [{did}] {nome} | CRO: {cro}")
    id_dent = utils.input_inteiro("  ID do dentista: ", 1)

    uf = input("  Filtrar por UF (opcional, Enter para todas): ").strip().upper()

    sql = """
        SELECT p.id, p.nome, p.cpf, p.data_nasc, p.telefone, p.email,
               p.cidade, p.uf, d.nome AS dentista_nome, d.cro
        FROM tdb_pacientes p
        INNER JOIN tdb_dentistas d ON d.id = p.id_dentista
        WHERE p.id_dentista = :id_dent
    """
    binds: dict = {"id_dent": id_dent}
    if uf:
        sql += " AND UPPER(p.uf) = :uf"
        binds["uf"] = uf
    sql += " ORDER BY p.nome"

    with database.cursor() as cur:
        cur.execute(sql, binds)
        colunas = [c[0].lower() for c in cur.description]
        linhas = [dict(zip(colunas, row)) for row in cur.fetchall()]

    _exibir_e_oferecer_export(
        titulo="Pacientes encontrados",
        dados=linhas,
        prefixo_arquivo=f"pacientes_dentista_{id_dent}",
        formatador=_formatar_paciente,
    )


def _formatar_paciente(p: dict) -> str:
    nasc = utils.formatar_data(p.get("data_nasc") or "")
    cidade_uf = f"{p.get('cidade') or '—'}/{p.get('uf') or '—'}"
    return (f"  [{p['id']}] {p['nome']} | Nasc.: {nasc} | "
            f"Tel.: {p.get('telefone') or '—'} | {cidade_uf} | "
            f"Dentista: Dr(a). {p['dentista_nome']}")


# ── Relatório 2: Atendimentos por status e período ────────

def relatorio_atendimentos_por_status_periodo() -> None:
    """SELECT/WHERE com filtro de status e BETWEEN nas datas."""
    utils.cabecalho("RELATÓRIO — ATENDIMENTOS POR STATUS E PERÍODO")

    print("  Status:")
    print("    [1] agendado")
    print("    [2] realizado")
    print("    [3] cancelado")
    print("    [4] (todos)")
    idx = utils.input_inteiro("  Opção: ", 1, 4)
    status_map = {1: "agendado", 2: "realizado", 3: "cancelado", 4: None}
    status = status_map[idx]

    data_inicio = utils.input_data("  Data inicial (DD/MM/AAAA): ")
    data_fim = utils.input_data("  Data final (DD/MM/AAAA): ")

    sql = """
        SELECT a.id, a.data, a.tipo, a.status, a.observacoes,
               p.nome AS paciente, d.nome AS dentista, c.nome AS campanha
        FROM tdb_atendimentos a
        INNER JOIN tdb_pacientes p ON p.id = a.id_paciente
        INNER JOIN tdb_dentistas d ON d.id = a.id_dentista
        LEFT  JOIN tdb_campanhas c ON c.id = a.id_campanha
        WHERE a.data BETWEEN :data_inicio AND :data_fim
    """
    binds: dict = {"data_inicio": data_inicio, "data_fim": data_fim}
    if status:
        sql += " AND a.status = :status"
        binds["status"] = status
    sql += " ORDER BY a.data"

    with database.cursor() as cur:
        cur.execute(sql, binds)
        colunas = [c[0].lower() for c in cur.description]
        linhas = [dict(zip(colunas, row)) for row in cur.fetchall()]

    rotulo_status = status or "todos"
    _exibir_e_oferecer_export(
        titulo=f"Atendimentos ({rotulo_status})",
        dados=linhas,
        prefixo_arquivo=f"atendimentos_{rotulo_status}",
        formatador=_formatar_atendimento,
    )


def _formatar_atendimento(a: dict) -> str:
    data = utils.formatar_data(a.get("data") or "")
    return (f"  [{a['id']}] {data} | {a['tipo']:<18} | {a['status']:<10} | "
            f"Paciente: {a['paciente']} | Dr(a). {a['dentista']} | "
            f"Campanha: {a.get('campanha') or '—'}")


# ── Relatório 3: Notificações a partir de uma data ────────

def relatorio_notificacoes_a_partir_de() -> None:
    """SELECT/WHERE com filtro temporal nas notificações."""
    utils.cabecalho("RELATÓRIO — NOTIFICAÇÕES A PARTIR DE UMA DATA")

    data_inicio = utils.input_data("  Data inicial (DD/MM/AAAA): ")

    sql = """
        SELECT n.id, n.data_envio, n.canal, n.mensagem,
               c.nome AS colaborador, d.nome AS dentista
        FROM tdb_notificacoes n
        LEFT JOIN tdb_colaboradores c ON c.id = n.id_colaborador
        LEFT JOIN tdb_dentistas    d ON d.id = n.id_dentista
        WHERE SUBSTR(n.data_envio, 1, 10) >= :data_inicio
        ORDER BY n.data_envio DESC
    """
    binds = {"data_inicio": data_inicio}

    with database.cursor() as cur:
        cur.execute(sql, binds)
        colunas = [c[0].lower() for c in cur.description]
        linhas = [dict(zip(colunas, row)) for row in cur.fetchall()]

    _exibir_e_oferecer_export(
        titulo="Notificações encontradas",
        dados=linhas,
        prefixo_arquivo="notificacoes",
        formatador=_formatar_notificacao,
    )


def _formatar_notificacao(n: dict) -> str:
    envio = (n.get("data_envio") or "")[:16]
    return (f"  [{n['id']}] {envio} | canal: {n['canal']:<6} | "
            f"Colab: {n.get('colaborador') or '—':<25} | "
            f"Dr(a). {n.get('dentista') or '—'}\n"
            f"        {n['mensagem']}")


# ── Helpers de exibição e exportação ──────────────────────

def _exibir_e_oferecer_export(titulo: str, dados: list[dict],
                               prefixo_arquivo: str, formatador) -> None:
    """Mostra o resultado em tela e pergunta se o usuário quer exportar."""
    utils.separador()
    print(f"  {titulo}: {len(dados)} registro(s)")
    utils.separador()
    if not dados:
        print("  Nenhum registro encontrado para os filtros informados.")
        utils.pausar()
        return

    for item in dados:
        print(formatador(item))

    utils.separador()
    if utils.confirmar("  Exportar resultado para JSON? (S/N): "):
        caminho = _exportar_json(dados, prefixo_arquivo)
        print(f"  Arquivo gerado: {caminho}")
    utils.pausar()


def _exportar_json(dados: list[dict], prefixo: str) -> str:
    os.makedirs(PASTA_EXPORT, exist_ok=True)
    carimbo = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome = f"{prefixo}_{carimbo}.json"
    caminho = os.path.join(PASTA_EXPORT, nome)
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=2, default=str)
    return caminho
