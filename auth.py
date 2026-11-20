"""
Exercício de Loop - Automação e Programabilidade de Redes
Aluno: Gabriel Soares (gabrielllss) - 5º semestre ADS

Reutilize aqui o código de autenticação da aula anterior.
Este módulo centraliza a obtenção do token Bearer.

Como usar:
  1. Defina a variável de ambiente API_TOKEN, ou
  2. Implemente a função login() com o código da aula anterior.

Exemplo da aula anterior (ajuste URL/credenciais conforme seu material):
  POST https://api.wagnerloch.com.br/auth/login
  body: {"email": "...", "password": "..."} -> {"token": "..."}
"""

import os


def get_token(token_arg: str | None = None) -> str:
    """
    Retorna o token Bearer para o desafio.
    Prioridade: argumento CLI > env API_TOKEN / TOKEN > erro explicativo.
    """
    if token_arg:
        return token_arg.strip()

    for var in ("API_TOKEN", "TOKEN", "BEARER_TOKEN"):
        v = os.getenv(var)
        if v and v.strip():
            return v.strip()

    raise SystemExit(
        "Token não encontrado.\n"
        "Forneça o token de uma das formas:\n"
        '  1) python loop_challenge.py --token "SEU_TOKEN"\n'
        "  2) export API_TOKEN='SEU_TOKEN'  (Linux/Mac)\n"
        "     set API_TOKEN=SEU_TOKEN      (Windows CMD)\n"
        "\nO token vem do código de autenticação da aula anterior."
    )


# TODO (opcional): cole aqui sua função de login da aula anterior, ex:
#
# import requests
# AUTH_URL = "https://api.wagnerloch.com.br/auth/login"
# def login(email: str, password: str) -> str:
#     r = requests.post(AUTH_URL, json={"email": email, "password": password}, timeout=15)
#     r.raise_for_status()
#     return r.json()["token"]
