import argparse
import csv
import http.client
import math
import os
import threading
import time
from urllib.parse import urlsplit
 
FIELDS = [
    "scenario", "url", "clients", "rep", "t_start", "t_end", "duration_s",
    "requests", "errors", "rps", "mean_ms", "p50_ms", "p95_ms", "p99_ms", "max_ms",
]
 
 
def percentile(sorted_vals, p):
    if not sorted_vals:
        return math.nan
    k = (len(sorted_vals) - 1) * p / 100
    lo = int(k)
    hi = min(lo + 1, len(sorted_vals) - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (k - lo)
 
 
def client(parts, method, record_from, stop_at, out):
    path = parts.path or "/"
    if parts.query:
        path += "?" + parts.query
    port = parts.port or 80
 
    def connect():
        return http.client.HTTPConnection(parts.hostname, port, timeout=120)
 
    conn = connect()
    samples = []
    while time.perf_counter() < stop_at:
        t0 = time.perf_counter()
        ok = False
        try:
            conn.request(method, path)
            resp = conn.getresponse()
            resp.read()
            ok = 200 <= resp.status < 300
        except Exception:
            conn.close()
            conn = connect()
        t1 = time.perf_counter()
        if t0 >= record_from:  # descarta o aquecimento
            samples.append((t1 - t0, ok))
    conn.close()
    out.append(samples)
 
 
def run_level(url, method, clients, warmup, duration):
    parts = urlsplit(url)
    start = time.perf_counter()
    epoch = time.time()
    record_from = start + warmup
    stop_at = record_from + duration
    out = []
    threads = [
        threading.Thread(target=client, args=(parts, method, record_from, stop_at, out))
        for _ in range(clients)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
 
    samples = [s for per_client in out for s in per_client]
    lat_ok = sorted(l * 1000 for l, ok in samples if ok)
    errors = sum(1 for _, ok in samples if not ok)
    return {
        "t_start": round(epoch + warmup, 3),
        "t_end": round(epoch + warmup + duration, 3),
        "duration_s": duration,
        "requests": len(lat_ok),
        "errors": errors,
        "rps": round(len(lat_ok) / duration, 3),
        "mean_ms": round(sum(lat_ok) / len(lat_ok), 2) if lat_ok else math.nan,
        "p50_ms": round(percentile(lat_ok, 50), 2),
        "p95_ms": round(percentile(lat_ok, 95), 2),
        "p99_ms": round(percentile(lat_ok, 99), 2),
        "max_ms": round(lat_ok[-1], 2) if lat_ok else math.nan,
    }
 
 
def main():
    ap = argparse.ArgumentParser(description="Gerador de carga com varredura de demanda")
    ap.add_argument("--url", required=True)
    ap.add_argument("--method", default="GET", choices=["GET", "POST"])
    ap.add_argument("--scenario", required=True, help="rótulo do cenário (ex.: 1cpu-1gb)")
    ap.add_argument("--levels", default="1,2,4,8,16,32", help="clientes simultâneos, separados por vírgula")
    ap.add_argument("--duration", type=float, default=30, help="segundos medidos por nível")
    ap.add_argument("--warmup", type=float, default=5, help="segundos descartados no início de cada nível")
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--pause", type=float, default=5, help="pausa entre execuções (s)")
    ap.add_argument("--out", required=True, help="CSV de saída (acrescenta se já existir)")
    args = ap.parse_args()
 
    levels = [int(x) for x in args.levels.split(",")]
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    new_file = not os.path.exists(args.out)
 
    with open(args.out, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            writer.writeheader()
        for rep in range(1, args.reps + 1):
            for clients in levels:
                m = run_level(args.url, args.method, clients, args.warmup, args.duration)
                row = {"scenario": args.scenario, "url": args.url, "clients": clients, "rep": rep, **m}
                writer.writerow(row)
                f.flush()
                print(
                    f"rep={rep} clientes={clients:<3} rps={m['rps']:<8} "
                    f"mean={m['mean_ms']}ms p95={m['p95_ms']}ms erros={m['errors']}",
                    flush=True,
                )
                time.sleep(args.pause)
 
 
if __name__ == "__main__":
    main()