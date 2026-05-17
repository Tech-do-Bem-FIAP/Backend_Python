"""
Tech do Bem — Sistema de Gestão Odontológica
Turma do Bem | FIAP 1TDS Agosto — Sprint 4

Integrantes:
  Hugo Souza de Jesus       (RM568542)
  Lucas Campanhã dos Santos (RM566815)
  Lucas Marcelino Pompeu    (RM567010)

Persistência: Oracle Database (FIAP) via biblioteca oracledb.
API externa: ViaCEP (https://viacep.com.br) para preenchimento de
             endereço durante o cadastro de pacientes.
"""

import sys

import oracledb

from modules import storage, utils
from modules.auth import fazer_login, submeter_solicitacao
from modules.painel_colaborador import menu_colaborador
from modules.painel_dentista import menu_dentista


# ── Seed inicial ──────────────────────────────────────────

def _seed_admin() -> None:
    """Garante que o usuário ADMIN exista ao iniciar o sistema."""
    colaboradores = storage.carregar("colaboradores")
    if not any(c["email"].upper() == "ADMIN" for c in colaboradores):
        colaboradores.append({
            "id": storage.proximo_id(colaboradores),
            "nome": "Administrador",
            "cpf": None,
            "email": "ADMIN",
            "senha": "ADMIN",
            "cargo": "Administrador",
            "disponibilidade": 1,
        })
        storage.salvar("colaboradores", colaboradores)


# ── Menu público ──────────────────────────────────────────

def menu_publico() -> None:
    while True:
        utils.cabecalho("TURMA DO BEM — Sistema de Gestão")
        print("  Bem-vindo(a)!\n")
        print("  [1] Fazer login")
        print("  [2] Solicitar cadastro (dentista ou colaborador)")
        print("  [0] Sair")

        opcao = utils.input_inteiro("  Opção: ", 0, 2)

        if opcao == 0:
            utils.cabecalho("TURMA DO BEM")
            print("  Obrigado por usar o sistema. Até logo!")
            break

        try:
            if opcao == 1:
                resultado = fazer_login()
                if resultado:
                    tipo, usuario = resultado
                    if tipo == "colaborador":
                        menu_colaborador(usuario)
                    else:
                        menu_dentista(usuario)
            elif opcao == 2:
                submeter_solicitacao()
        except oracledb.DatabaseError as exc:
            print(f"\n  [ERRO] Falha de banco de dados: {exc}")
            utils.pausar()


# ── Entry point ───────────────────────────────────────────

if __name__ == "__main__":
    try:
        storage.inicializar()
    except (RuntimeError, oracledb.DatabaseError) as exc:
        print(f"\n  [FATAL] {exc}")
        print("  Verifique se você executou o Oracle_Scripts.sql e se está")
        print("  conectado à rede/VPN da FIAP. Encerrando.\n")
        sys.exit(1)

    try:
        _seed_admin()
        menu_publico()
    except KeyboardInterrupt:
        print("\n  Encerrado pelo usuário.")
