#!/bin/bash
# Balanceo de carga dinámico: escala el número de réplicas de la app web.
# Nginx (servicio "lb") reparte las peticiones entre todas las réplicas.
# Uso:
#   ./scale.sh 3     -> 3 réplicas
#   ./scale.sh 1     -> 1 réplica
set -e
cd "$(dirname "$0")"

N="${1:-2}"

docker compose -f docker-compose.aws.yml up -d --scale web="$N"

echo ""
echo "=============================================================="
echo " web escalado a $N réplica(s)."
echo " Nginx balancea la carga automáticamente (round-robin dinámico)."
echo " Revisa: docker compose -f docker-compose.aws.yml ps"
echo "=============================================================="
