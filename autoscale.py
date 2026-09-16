#!/usr/bin/env python3
"""
Auto-escalado dinámico de réplicas web basado en carga (CPU).

Implementa un mecanismo de balanceo de carga DINÁMICO de cero costo:
  - Nginx reparte las peticiones entre las réplicas (round-robin).
  - Este controlador monitorea la CPU promedio de las réplicas y
    escala horizontalmente (sube/baja réplicas) en tiempo real.

Ejecutar en la EC2:
  python3 autoscale.py

Umbrales configurables mediante variables de entorno:
  MIN_REPLICAS, MAX_REPLICAS, CPU_UP, CPU_DOWN, INTERVALO
"""

import os
import subprocess
import sys
import time

COMPOSE = "docker-compose.aws.yml"
MIN = int(os.environ.get("MIN_REPLICAS", "1"))
MAX = int(os.environ.get("MAX_REPLICAS", "4"))
CPU_UP = float(os.environ.get("CPU_UP", "70"))     # % de CPU para escalar arriba
CPU_DOWN = float(os.environ.get("CPU_DOWN", "20")) # % de CPU para escalar abajo
INTERVALO = int(os.environ.get("INTERVALO", "10")) # segundos entre revisiones


def cpu_por_replica():
    """Devuelve una lista con el % de CPU de cada réplica web."""
    cmd = ["docker", "stats", "--no-stream", "--format", "{{.Name}} {{.CPUPerc}}"]
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    cpus = []
    for line in out.splitlines():
        if "web" in line:
            try:
                cpus.append(float(line.split()[-1].rstrip("%")))
            except ValueError:
                pass
    return cpus


def numero_replicas():
    cmd = ["docker", "compose", "-f", COMPOSE, "ps", "-q", "web"]
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    return len([l for l in out.splitlines() if l.strip()])


def escalar(n):
    subprocess.run(
        ["docker", "compose", "-f", COMPOSE, "up", "-d", "--scale", f"web={n}"],
        check=True,
        stdout=subprocess.DEVNULL,
    )


def main():
    print(f"[auto-scaler] Iniciado. min={MIN} max={MAX} subir>{CPU_UP}% bajar<{CPU_DOWN}%")
    try:
        while True:
            cpus = cpu_por_replica()
            if cpus:
                promedio = sum(cpus) / len(cpus)
                n = numero_replicas()
                if promedio > CPU_UP and n < MAX:
                    print(f"[{time.strftime('%H:%M:%S')}] CPU {promedio:.0f}% > {CPU_UP:.0f}% -> escalando a {n + 1}")
                    escalar(n + 1)
                elif promedio < CPU_DOWN and n > MIN:
                    print(f"[{time.strftime('%H:%M:%S')}] CPU {promedio:.0f}% < {CPU_DOWN:.0f}% -> reduciendo a {n - 1}")
                    escalar(n - 1)
                else:
                    print(f"[{time.strftime('%H:%M:%S')}] CPU {promedio:.0f}% · {n} réplica(s) · estable")
            time.sleep(INTERVALO)
    except KeyboardInterrupt:
        print("\n[auto-scaler] Detenido.")


if __name__ == "__main__":
    main()
