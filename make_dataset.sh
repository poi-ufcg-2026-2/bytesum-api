```bash
#!/bin/bash

BASE_DIR=$(dirname -- "$(readlink -f -- "$0")")
PYTHON="$BASE_DIR/.venv/bin/python"

if [ ! -x "$PYTHON" ]; then
  echo "Ambiente virtual não encontrado. Rode ./build.sh primeiro." >&2
  exit 1
fi

cd "$BASE_DIR" || exit 1
exec "$PYTHON" src/make_dataset.py --dir "${DATASET_DIR:-$BASE_DIR/dataset}" "$@"
```