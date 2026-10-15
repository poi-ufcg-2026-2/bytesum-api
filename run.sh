```bash
#!/bin/bash

BASE_DIR=$(dirname -- "$(readlink -f -- "$0")")

if [ ! -x "$BASE_DIR/.venv/bin/uvicorn" ]; then
  echo "Ambiente virtual não encontrado. Rode ./build.sh primeiro." >&2
  exit 1
fi

export DATASET_DIR="${DATASET_DIR:-$BASE_DIR/dataset}"
export WRITE_DIR="${WRITE_DIR:-$BASE_DIR/written}"

if [ ! -d "$DATASET_DIR" ] || [ -z "$(ls -A "$DATASET_DIR" 2>/dev/null)" ]; then
  echo "Aviso: dataset vazio em $DATASET_DIR. Rode ./make_dataset.sh." >&2
fi

exec "$BASE_DIR/.venv/bin/uvicorn" app:app \
  --app-dir "$BASE_DIR/src" \
  --host "${HOST:-0.0.0.0}" \
  --port "${PORT:-8000}" \
  --workers "${WORKERS:-1}"
```