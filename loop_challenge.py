"""
Loop Challenge - Guia de Implementação (prof. Wagner Loch)
Aluno: Gabriel Soares (gabrielllss) - 5º semestre ADS

Fluxo:
  1. POST https://api.wagnerloch.com.br/challenges/loop
     Headers: Authorization: Bearer <token>
     Body: {"maxIterations": 10}
  2. Resposta START -> aguardar nextWaitTimeInSeconds
  3. Repetir POST (sem body ou com mesmo body) até SUCCESS
  4. TOO_EARLY / TOO_LATE = desafio resetado -> recomeçar do zero

Uso:
  pip install -r requirements.txt
  python loop_challenge.py --token SEU_TOKEN --max-iterations 10
  python loop_challenge.py --token SEU_TOKEN --max-iterations 5 --buffer 1.0 --verbose
"""

import argparse
import logging
import sys
import time
from datetime import datetime

import requests

from auth import get_token

API_URL = "https://api.wagnerloch.com.br/challenges/loop"
REQUEST_TIMEOUT = 15  # segundos para cada requisição HTTP


def setup_logger(verbose: bool) -> logging.Logger:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stdout,
    )
    return logging.getLogger("loop-challenge")


def do_request(session: requests.Session, token: str, max_iterations: int | None, log: logging.Logger) -> dict:
    """Faz um POST no endpoint do desafio e retorna o JSON."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    # Na primeira requisição enviamos maxIterations.
    # Nas seguintes, repetimos o mesmo body (a API ignora após o START).
    payload = {"maxIterations": max_iterations} if max_iterations else {}
    started = time.monotonic()
    resp = session.request("POST", API_URL, headers=headers, json=payload or None, timeout=REQUEST_TIMEOUT)
    elapsed = time.monotonic() - started
    log.debug(f"HTTP {resp.status_code} em {elapsed:.2f}s | body={resp.text[:500]}")
    try:
        resp.raise_for_status()
    except requests.HTTPError:
        # Tenta extrair JSON de erro da API antes de estourar
        try:
            log.error(f"Erro HTTP: {resp.text[:1000]}")
        finally:
            raise
    try:
        return resp.json()
    except ValueError:
        raise RuntimeError(f"Resposta não-JSON da API: {resp.text[:500]}")


def precise_sleep(seconds: float, log: logging.Logger) -> None:
    """
    Espera precisa usando monotonic + wakeup progressivo.
    Evita drift do time.sleep() longo e permite log.
    """
    if seconds <= 0:
        return
    log.info(f"Aguardando {seconds:.1f}s antes da próxima requisição...")
    deadline = time.monotonic() + seconds
    # Dorme em fatias para ser interrompível com Ctrl+C e mais preciso no fim
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        # nos últimos 2s, fatias curtas para acertar o alvo
        time.sleep(min(remaining, 0.2 if remaining < 2 else 1.0))


def run_challenge(token: str, max_iterations: int, buffer: float, log: logging.Logger) -> bool:
    """
    Executa o desafio até SUCCESS.
    Retorna True se concluiu, False se precisa recomeçar (reset).
    buffer: segundos extras somados ao nextWaitTimeInSeconds para compensar
            latência de rede e evitar TOO_EARLY (ex: 0.8 a 1.2s).
    """
    session = requests.Session()
    # Retry simples para falhas de rede (sem biblioteca extra)
    attempt = 0
    while True:
        attempt += 1
        try:
            data = do_request(session, token, max_iterations if attempt == 1 else None, log)
        except (requests.ConnectionError, requests.Timeout) as e:
            log.warning(f"Falha de rede (tentativa {attempt}): {e}. Tentando de novo em 3s...")
            time.sleep(3)
            if attempt > 10:
                log.error("Muitas falhas de rede seguidas. Abortando.")
                raise
            continue
        status = str(data.get("status", "")).upper()
        msg = data.get("message", "")
        progress = data.get("progress", "")
        wait = data.get("nextWaitTimeInSeconds")

        print(f"[{datetime.now():%H:%M:%S}] status={status} {progress} | {msg}")

        if status == "SUCCESS":
            log.info("🎉 Parabéns! Você completou o desafio de loop com sucesso!")
            return True

        if status in ("TOO_EARLY", "TOO_LATE"):
            log.warning(f"⚠️ {status}: {msg} -> desafio resetado, recomeçando...")
            return False

        if status in ("START", "CONTINUE"):
            try:
                wait_s = float(wait)
            except (TypeError, ValueError):
                log.error(f"Resposta sem nextWaitTimeInSeconds válido: {data}. Recomeçando...")
                return False
            # Compensação de latência: soma buffer para não chegar cedo
            total_wait = wait_s + buffer
            log.info(f"Progresso {progress} | próxima em {wait_s}s (+{buffer}s buffer = {total_wait:.1f}s)")
            precise_sleep(total_wait, log)
            attempt = 0  # zera contador de retry após sucesso
            # mantém max_iterations=None nas próximas iterações do mesmo ciclo
            max_iterations_inner = None

            # loop interno: continua pedindo até SUCCESS ou RESET
            while True:
                attempt += 1
                try:
                    data = do_request(session, token, None, log)
                except (requests.ConnectionError, requests.Timeout) as e:
                    log.warning(f"Falha de rede: {e}. Nova tentativa em 3s...")
                    time.sleep(3)
                    continue
                status = str(data.get("status", "")).upper()
                msg = data.get("message", "")
                progress = data.get("progress", "")
                wait = data.get("nextWaitTimeInSeconds")
                print(f"[{datetime.now():%H:%M:%S}] status={status} {progress} | {msg}")

                if status == "SUCCESS":
                    log.info("🎉 Desafio concluído com sucesso!")
                    return True
                if status in ("TOO_EARLY", "TOO_LATE"):
                    log.warning(f"⚠️ {status}: {msg} -> resetado, recomeçando do zero...")
                    return False
                if status == "CONTINUE":
                    try:
                        wait_s = float(wait)
                    except (TypeError, ValueError):
                        log.error(f"CONTINUE sem tempo válido: {data}")
                        return False
                    total_wait = wait_s + buffer
                    log.info(f"Progresso {progress} | próxima em {wait_s}s (+buffer = {total_wait:.1f}s)")
                    precise_sleep(total_wait, log)
                    continue
                log.error(f"Status inesperado: {data}")
                return False
        else:
            log.error(f"Resposta inesperada da API: {data}")
            return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Loop Challenge - Automação e Programabilidade de Redes (Gabriel Soares)")
    parser.add_argument("--token", default=None, help="Bearer token (ou use env API_TOKEN)")
    parser.add_argument("--max-iterations", type=int, default=10, help="maxIterations da 1ª requisição (padrão: 10)")
    parser.add_argument("--buffer", type=float, default=1.0, help="segundos extras p/ compensar latência (padrão: 1.0)")
    parser.add_argument("--retries", type=int, default=3, help="tentativas completas após reset TOO_EARLY/TOO_LATE (padrão: 3, 0=infinito)")
    parser.add_argument("--verbose", action="store_true", help="log detalhado (debug)")
    args = parser.parse_args()

    log = setup_logger(args.verbose)
    token = get_token(args.token)

    log.info(f"Iniciando Loop Challenge | maxIterations={args.max_iterations} | buffer={args.buffer}s")
    log.info(f"Aluno: Gabriel Soares | API: {API_URL}")

    tries = 0
    while True:
        tries += 1
        if args.retries and tries > args.retries and args.retries > 0:
            # Na verdade 'tries' conta ciclos; permite args.retries resets
            pass
        ok = run_challenge(token, args.max_iterations, args.buffer, log)
        if ok:
            break
        log.info(f"Reiniciando desafio (ciclo {tries + 1})...")
        if args.retries > 0 and tries >= args.retries:
            log.error(f"Limite de {args.retries} ciclos atingido. Ajuste o --buffer e tente de novo.")
            sys.exit(2)
        time.sleep(2)  # pequena pausa antes de recomeçar após reset


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrompido pelo usuário (Ctrl+C).")
        sys.exit(130)
