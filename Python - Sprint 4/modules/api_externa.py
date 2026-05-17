"""
api_externa.py — Consumo da API pública ViaCEP.

ViaCEP (https://viacep.com.br) é um serviço gratuito brasileiro que
devolve dados de endereço (logradouro, bairro, cidade, UF) a partir de
um CEP. É usado neste sistema para preencher automaticamente o endereço
de pacientes e dentistas durante o cadastro.

Utiliza apenas a biblioteca padrão (urllib + json) — não exige nenhuma
dependência externa adicional.
"""

from __future__ import annotations

import json
import re
from urllib import error, request

URL_BASE = "https://viacep.com.br/ws/{cep}/json/"
TIMEOUT_SEG = 5

_CEP_RE = re.compile(r"^\d{5}-?\d{3}$")


def _normalizar_cep(cep: str) -> str | None:
    """Remove hifens/espaços e valida que o CEP tem 8 dígitos."""
    if not cep:
        return None
    apenas_digitos = re.sub(r"\D", "", cep)
    if len(apenas_digitos) != 8:
        return None
    return apenas_digitos


def buscar_endereco(cep: str) -> dict | None:
    """
    Consulta o ViaCEP e devolve um dict com as chaves padronizadas:
        {"cep", "logradouro", "bairro", "cidade", "uf"}
    Retorna None em caso de CEP inválido, não encontrado ou erro de rede.
    """
    normalizado = _normalizar_cep(cep)
    if not normalizado:
        print("  [API] CEP inválido (use 8 dígitos).")
        return None

    url = URL_BASE.format(cep=normalizado)
    try:
        with request.urlopen(url, timeout=TIMEOUT_SEG) as resposta:
            payload = json.loads(resposta.read().decode("utf-8"))
    except error.URLError as exc:
        print(f"  [API] Falha de rede ao consultar ViaCEP: {exc.reason}")
        return None
    except (ValueError, TimeoutError) as exc:
        print(f"  [API] Resposta inválida do ViaCEP: {exc}")
        return None

    if payload.get("erro"):
        print("  [API] CEP não encontrado na base do ViaCEP.")
        return None

    return {
        "cep": payload.get("cep") or _formatar_cep(normalizado),
        "logradouro": payload.get("logradouro") or "",
        "bairro": payload.get("bairro") or "",
        "cidade": payload.get("localidade") or "",
        "uf": payload.get("uf") or "",
    }


def _formatar_cep(digitos: str) -> str:
    return f"{digitos[:5]}-{digitos[5:]}"


def coletar_endereco_interativo(prompt: str = "  CEP (Enter para pular): ") -> dict:
    """
    Pergunta um CEP ao usuário, busca os dados no ViaCEP e devolve um
    dict com as chaves de endereço. Em caso de erro ou Enter vazio,
    devolve um dict com strings vazias para todos os campos.
    """
    vazio = {"cep": "", "logradouro": "", "bairro": "", "cidade": "", "uf": ""}
    cep = input(prompt).strip()
    if not cep:
        return vazio

    endereco = buscar_endereco(cep)
    if not endereco:
        return vazio

    print(f"  Endereço encontrado: {endereco['logradouro']}, "
          f"{endereco['bairro']} — {endereco['cidade']}/{endereco['uf']}")
    return endereco
