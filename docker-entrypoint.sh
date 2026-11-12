#!/bin/sh
set -e
mkdir -p "$DATASET_DIR" "$WRITE_DIR" "$LOG_DIR"

# Gera o dataset pequeno se ainda não existir (a app lê o dataset na inicialização)
if [ -z "$(ls -A "$DATASET_DIR")" ]; then
  python src/make_dataset.py --dir "$DATASET_DIR" --count 20 --min-mb 1 --max-mb 4
fi

# Logs vão para o volume montado em $LOG_DIR
exec uvicorn app:app --app-dir /app/src \
  --host 0.0.0.0 --port "${PORT}" --workers "${WORKERS:-1}" \
  >> "$LOG_DIR/application.log" 2>&1