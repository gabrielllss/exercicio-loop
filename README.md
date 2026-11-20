# Exercício de Loop — Automação e Programabilidade de Redes

**Aluno:** Gabriel Soares (gabrielllss) — 5º semestre ADS

Script em Python que realiza requisições HTTP em intervalos específicos de tempo,
conforme o [guia do professor](https://github.com/wagnerloch/Automa-o-e-Programabilidade-em-Redes/blob/main/exercicio-loop.md).

## Endpoint

- URL: `https://api.wagnerloch.com.br/challenges/loop`
- Método: `POST`
- Header: `Authorization: Bearer <seu-token>`
- Body inicial: `{"maxIterations": 10}`

## Como executar

```bash
pip install -r requirements.txt

# Opção 1: token via argumento
python loop_challenge.py --token SEU_TOKEN --max-iterations 10

# Opção 2: token via variável de ambiente
export API_TOKEN='SEU_TOKEN'   # Linux/Mac
# set API_TOKEN=SEU_TOKEN      # Windows CMD
python loop_challenge.py --max-iterations 10

# Com buffer de latência e log detalhado
python loop_challenge.py --token SEU_TOKEN --buffer 1.0 --verbose
```

## Opções

| Flag | Padrão | Descrição |
|------|--------|-----------|
| `--token` | env `API_TOKEN` | Bearer token (código de autenticação da aula anterior) |
| `--max-iterations` | 10 | Nº máximo de iterações da 1ª requisição (servidor sorteia 2..max) |
| `--buffer` | 1.0 | Segundos extras somados ao `nextWaitTimeInSeconds` p/ compensar latência e evitar `TOO_EARLY` |
| `--retries` | 3 | Ciclos completos após reset (`TOO_EARLY`/`TOO_LATE`). `0` = tentar sem limite |
| `--verbose` | off | Log detalhado (debug) |

## Como funciona

1. Faz `POST` inicial com `maxIterations`.
2. Recebe `START` com `nextWaitTimeInSeconds` (5–60s) e `progress` (ex: `1 / 5`).
3. Aguarda `nextWaitTimeInSeconds + buffer` com espera precisa (`time.monotonic`).
4. Repete `POST` até receber `SUCCESS`.
5. Se receber `TOO_EARLY` / `TOO_LATE`, o desafio foi resetado → recomeça automaticamente.

## Estrutura

- `loop_challenge.py` — script principal (loops, temporização, logs, retry, CLI)
- `auth.py` — centraliza o token (reutilize aqui o código de autenticação da aula anterior)
- `requirements.txt` — dependências (`requests`)

## Dicas do professor implementadas

- ✅ Logs com timestamp para debug
- ✅ Compensação automática de latência (`--buffer`)
- ✅ Retry para falhas de rede
- ✅ Interface de linha de comando configurável
- ✅ Tratamento de `TOO_EARLY` / `TOO_LATE` com restart automático
