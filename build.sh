#!/bin/bash

BASE_DIR=$(dirname -- "$(readlink -f -- "$0")")

if ! python3 -c "import venv, ensurepip" 2>/dev/null; then
  echo "python3-venv não encontrado. Instale com: sudo apt install python3-venv python3-pip"
  exit 1
fi

python3 -m venv "$BASE_DIR/.venv" || exit 1
"$BASE_DIR/.venv/bin/pip" install --upgrade pip -q || exit 1
"$BASE_DIR/.venv/bin/pip" install -r "$BASE_DIR/requirements.txt" || exit 1

echo "Build concluído. Gere o dataset com ./src/make_dataset.py e inicie com ./run.sh"
