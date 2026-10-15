# Bytesum API — IO-bound

Aplicação web usando FastAPI com perfil **IO-bound**, criado para a atividade 2 - Demanda, 
Provisionamento e Desempenho. A aplicação soma os bytes de arquivos de um dataset em 
disco e também grava arquivos com `fsync`.

Requer Python 3.10+ e `python3-venv` (`sudo apt install python3-venv python3-pip`).

## Executar

```bash
./build.sh                  # cria .venv e instala as dependências
./src/make_dataset.py       # gera o dataset em ./dataset
./run.sh                    # porta 80
```

O gerador também pode ser executado com `python3 src/make_dataset.py` ou `./.venv/bin/python src/make_dataset.py` depois do build. Ele usa apenas a biblioteca padrão do Python.

Para testar na máquina local com um dataset pequeno:

```bash
./src/make_dataset.py --count 20 --min-mb 1 --max-mb 4
```

O gerador aceita `--dir`, `--count`, `--min-mb`, `--max-mb` e `--seed`. O padrão é 200 arquivos de 5 a 15 MB; `DATASET_DIR` pode definir o diretório de saída.

O dataset é lido na inicialização do servidor: se for gerado depois, reinicie o `./run.sh`.

Variáveis opcionais do `run.sh`:

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `PORT` | `80` | Porta HTTP |
| `HOST` | `0.0.0.0` | Interface de escuta |
| `WORKERS` | `1` | Processos do servidor (uvicorn `--workers`) |
| `THREAD_LIMIT` | `40` | Requisições processadas em paralelo por worker |
| `DATASET_DIR` | `./dataset` | Diretório com os arquivos de leitura |
| `WRITE_DIR` | `./written` | Diretório das gravações do `/write` |
| `CHUNK_SIZE_KB` | `1024` | Tamanho do bloco de leitura/escrita |
| `MAX_FILES_PER_REQUEST` | `20` | Limite do parâmetro `files` do `/sum` |
| `MAX_WRITE_KB` | `65536` | Limite do parâmetro `size_kb` do `/write` |

Exemplo: `WORKERS=2 THREAD_LIMIT=8 PORT=8080 ./run.sh`

## Endpoints

| Método | Rota | Parâmetros | Descrição |
|--------|------|------------|-----------|
| GET | `/health` | | Estado da aplicação e do dataset |
| GET | `/sum` | `files` (1 a 20; padrão 1), `nocache` (padrão `false`) | Soma os bytes de N arquivos sorteados do dataset (leitura) |
| POST | `/write` | `size_kb` (padrão 1024), `fsync` (padrão `true`), `keep` (padrão `false`) | Grava um arquivo novo, com `fsync` opcional (escrita) |

```bash
curl http://localhost/health
curl "http://localhost/sum?files=3"
curl "http://localhost/sum?files=3&nocache=true"
curl -X POST "http://localhost/write?size_kb=4096"
```

Resposta do `/sum`: lista com `file`, `bytes` e `sum` de cada arquivo, além de `total_bytes`, `nocache`
e `elapsed_ms` (tempo gasto no handler). O `/write` devolve `file`, `bytes`, `sum`, `fsync`, `kept` e `elapsed_ms`.
Parâmetros fora dos limites recebem `422`; `/sum` com dataset vazio recebe `503`.

A documentação interativa fica em `http://localhost/docs`.

## Estrutura

```
bytesum-api/
├── build.sh            
├── run.sh              
├── requirements.txt
└── src/
    ├── app.py           
    └── make_dataset.py  
```

`dataset/` e `written/` são criados na raiz e não são versionados.
