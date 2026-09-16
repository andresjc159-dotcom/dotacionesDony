"""Prueba de carga simple: mide rendimiento de la app con 1 y con N workers."""

import concurrent.futures
import statistics
import sys
import time

import requests

URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8090/"
N = int(sys.argv[2]) if len(sys.argv) > 2 else 400
C = int(sys.argv[3]) if len(sys.argv) > 3 else 20


def hit(_):
    t0 = time.perf_counter()
    r = requests.get(URL, timeout=10)
    return time.perf_counter() - t0, r.status_code


start = time.perf_counter()
with concurrent.futures.ThreadPoolExecutor(max_workers=C) as ex:
    results = list(ex.map(hit, range(N)))
total = time.perf_counter() - start

lat = [x[0] for x in results]
ok = sum(1 for x in results if x[1] == 200)
lat.sort()

print(f"URL: {URL}")
print(f"Peticiones: {N}  |  Concurrencia: {C}")
print(f"Correctas (200): {ok}/{N}")
print(f"Tiempo total: {total:.2f} s")
print(f"Throughput: {N/total:.1f} req/s")
print(f"Latencia promedio: {statistics.mean(lat)*1000:.1f} ms")
print(f"Latencia p95: {lat[int(len(lat)*0.95)]*1000:.1f} ms")
