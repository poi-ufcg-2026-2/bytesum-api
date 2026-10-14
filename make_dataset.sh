#!/bin/bash
 
BASE_DIR=$(dirname -- "$(readlink -f -- "$0")")
 
if [ ! -x "$BASE_DIR/.venv/bin/python" ]; then
  echo "Ambiente virtual não encontrado. Rode ./build.sh primeiro."
  exit 1
fi
 
cd "$BASE_DIR" || exit 1
"$BASE_DIR/.venv/bin/python" src/make_dataset.py --dir "${DATASET_DIR:-$BASE_DIR/dataset}" "$@"