import argparse
import csv
import os
import time
 
import psutil
 
MB = 1024 * 1024
FIELDS = [
    "timestamp", "cpu_pct", "cpu_user", "cpu_system", "cpu_iowait", "cpu_idle",
    "mem_used_mb", "mem_available_mb", "mem_cached_mb", "swap_used_mb",
    "disk_read_mbps", "disk_write_mbps", "load1",
]
 
 
def main():
    ap = argparse.ArgumentParser(description="Monitor de CPU, memória e disco")
    ap.add_argument("--out", required=True)
    ap.add_argument("--interval", type=float, default=1.0)
    args = ap.parse_args()
 
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    new_file = not os.path.exists(args.out)
 
    psutil.cpu_percent(None)        # inicializa os contadores
    psutil.cpu_times_percent(None)
    prev_disk = psutil.disk_io_counters()
    prev_t = time.time()
 
    with open(args.out, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            writer.writeheader()
        print(f"Monitorando a cada {args.interval}s em {args.out} (Ctrl+C para encerrar)")
        try:
            while True:
                time.sleep(args.interval)
                now = time.time()
                dt = now - prev_t
                prev_t = now
 
                ct = psutil.cpu_times_percent(None)
                vm = psutil.virtual_memory()
                disk = psutil.disk_io_counters()
                read_mbps = write_mbps = 0.0
                if disk and prev_disk:
                    read_mbps = (disk.read_bytes - prev_disk.read_bytes) / MB / dt
                    write_mbps = (disk.write_bytes - prev_disk.write_bytes) / MB / dt
                prev_disk = disk
 
                writer.writerow({
                    "timestamp": round(now, 3),
                    "cpu_pct": psutil.cpu_percent(None),
                    "cpu_user": ct.user,
                    "cpu_system": ct.system,
                    "cpu_iowait": getattr(ct, "iowait", 0.0),
                    "cpu_idle": ct.idle,
                    "mem_used_mb": round((vm.total - vm.available) / MB, 1),
                    "mem_available_mb": round(vm.available / MB, 1),
                    "mem_cached_mb": round(getattr(vm, "cached", 0) / MB, 1),
                    "swap_used_mb": round(psutil.swap_memory().used / MB, 1),
                    "disk_read_mbps": round(read_mbps, 2),
                    "disk_write_mbps": round(write_mbps, 2),
                    "load1": round(os.getloadavg()[0], 2) if hasattr(os, "getloadavg") else 0.0,
                })
                f.flush()
        except KeyboardInterrupt:
            print("Encerrado.")
 
 
if __name__ == "__main__":
    main()