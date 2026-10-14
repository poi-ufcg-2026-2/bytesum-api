import os
import random
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import anyio.to_thread
import numpy as np
from fastapi import FastAPI, HTTPException, Query

DATASET_DIR = Path(os.getenv("DATASET_DIR", "dataset"))
WRITE_DIR = Path(os.getenv("WRITE_DIR", "written"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE_KB", "1024")) * 1024
MAX_FILES = int(os.getenv("MAX_FILES_PER_REQUEST", "20"))
MAX_WRITE_KB = int(os.getenv("MAX_WRITE_KB", "65536"))
THREAD_LIMIT = int(os.getenv("THREAD_LIMIT", "40"))

BLOCK = os.urandom(CHUNK_SIZE)
BLOCK_SUM = int(np.frombuffer(BLOCK, dtype=np.uint8).sum(dtype=np.uint64))

dataset_files: list[Path] = []
dataset_bytes = 0


@asynccontextmanager
async def lifespan(app: FastAPI):
    global dataset_files, dataset_bytes
    anyio.to_thread.current_default_thread_limiter().total_tokens = THREAD_LIMIT

    WRITE_DIR.mkdir(parents=True, exist_ok=True)
    if DATASET_DIR.is_dir():
        dataset_files = sorted(p for p in DATASET_DIR.iterdir() if p.is_file())
        dataset_bytes = sum(p.stat().st_size for p in dataset_files)
    yield


app = FastAPI(title="bytesum-api", lifespan=lifespan)


def _drop_cache(fd: int) -> None:
    """Pede ao kernel para descartar as paginas do arquivo do page cache (Linux)."""
    if hasattr(os, "posix_fadvise"):
        os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)


def sum_file(path: Path, nocache: bool) -> tuple[int, int]:
    """Le o arquivo em blocos e retorna (tamanho_em_bytes, soma_dos_bytes)."""
    total = 0
    size = 0
    fd = os.open(path, os.O_RDONLY)
    try:
        if nocache:
            _drop_cache(fd)  
        while True:
            chunk = os.read(fd, CHUNK_SIZE)
            if not chunk:
                break
            size += len(chunk)
            total += int(np.frombuffer(chunk, dtype=np.uint8).sum(dtype=np.uint64))
        if nocache:
            _drop_cache(fd)  
    finally:
        os.close(fd)
    return size, total


def write_file(size_kb: int, fsync: bool, keep: bool) -> dict:
    """Grava size_kb KB de dados em um arquivo novo; opcionalmente faz fsync e apaga."""
    total_bytes = size_kb * 1024
    full, rem = divmod(total_bytes, len(BLOCK))
    checksum = full * BLOCK_SUM
    if rem:
        checksum += int(np.frombuffer(BLOCK[:rem], dtype=np.uint8).sum(dtype=np.uint64))

    path = WRITE_DIR / f"{uuid.uuid4().hex}.bin"
    with open(path, "wb") as f:
        for _ in range(full):
            f.write(BLOCK)
        if rem:
            f.write(BLOCK[:rem])
        f.flush()
        if fsync:
            os.fsync(f.fileno()) 
    if not keep:
        os.unlink(path)
    return {"file": path.name, "bytes": total_bytes, "sum": checksum, "kept": keep}


@app.get("/health")
def health():
    return {
        "status": "ok",
        "dataset_files": len(dataset_files),
        "dataset_bytes": dataset_bytes,
        "chunk_size_kb": CHUNK_SIZE // 1024,
        "thread_limit": THREAD_LIMIT,
        "pid": os.getpid(),
    }


@app.get("/sum")
def sum_endpoint(
    files: int = Query(1, ge=1, le=MAX_FILES, description="Quantidade de arquivos sorteados"),
    nocache: bool = Query(False, description="Descarta o page cache (leitura sempre do disco)"),
):
    if not dataset_files:
        raise HTTPException(
            status_code=503,
            detail="Dataset vazio. Rode: python make_dataset.py",
        )
    start = time.perf_counter()
    chosen = random.sample(dataset_files, min(files, len(dataset_files)))
    results = []
    total_bytes = 0
    for path in chosen:
        size, total = sum_file(path, nocache)
        total_bytes += size
        results.append({"file": path.name, "bytes": size, "sum": total})
    return {
        "files": results,
        "total_bytes": total_bytes,
        "nocache": nocache,
        "elapsed_ms": round((time.perf_counter() - start) * 1000, 2),
    }


@app.post("/write")
def write_endpoint(
    size_kb: int = Query(1024, ge=1, le=MAX_WRITE_KB, description="Tamanho do arquivo em KB"),
    fsync: bool = Query(True, description="Faz fsync apos gravar"),
    keep: bool = Query(False, description="Mantem o arquivo gravado (senao e apagado)"),
):
    start = time.perf_counter()
    result = write_file(size_kb, fsync, keep)
    result["fsync"] = fsync
    result["elapsed_ms"] = round((time.perf_counter() - start) * 1000, 2)
    return result