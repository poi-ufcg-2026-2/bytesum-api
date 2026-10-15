#!/usr/bin/env python3

import argparse
import os
import random
import sys
from pathlib import Path

BLOCK = 1024 * 1024  # 1 MB


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera arquivos aleatorios para o bytesum-api")
    parser.add_argument(
        "--dir",
        default=os.getenv("DATASET_DIR", "dataset"),
        help="diretorio de saida (padrao: DATASET_DIR ou ./dataset)",
    )
    parser.add_argument("--count", type=int, default=200, help="quantidade de arquivos")
    parser.add_argument("--min-mb", type=int, default=5, help="tamanho minimo (MB)")
    parser.add_argument("--max-mb", type=int, default=15, help="tamanho maximo (MB)")
    parser.add_argument("--seed", type=int, default=42, help="semente dos tamanhos (reprodutibilidade)")
    args = parser.parse_args()

    if args.min_mb < 1 or args.max_mb < args.min_mb or args.count < 1:
        parser.error("count e min-mb devem ser positivos; max-mb deve ser >= min-mb")

    out = Path(args.dir)
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)

    total = 0
    for i in range(1, args.count + 1):
        size = rng.randint(args.min_mb * BLOCK, args.max_mb * BLOCK)
        path = out / f"file.{i}"
        total += size
        if path.exists() and path.stat().st_size == size:
            continue  
        with open(path, "wb") as f:
            remaining = size
            while remaining > 0:
                n = min(BLOCK, remaining)
                f.write(os.urandom(n))
                remaining -= n
        if i % 10 == 0 or i == args.count:
            print(f"{i}/{args.count} arquivos ({total / 1024**3:.2f} GB)", flush=True)

    print(f"Dataset pronto em '{out}': {args.count} arquivos, {total / 1024**3:.2f} GB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
