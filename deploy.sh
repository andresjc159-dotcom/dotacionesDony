#!/bin/bash
# Despliegue CERO COSTO en una instancia EC2 (free tier).
# Todo corre en contenedores: web + worker + PostgreSQL + Redis.
#   chmod +x deploy.sh && ./deploy.sh
set -e
cd "$(dirname "$0")"

if ! command -v docker >/dev/null 2>&1; then
  echo ">> Instalando Docker..."
  curl -fsSL https://get.docker.com | sh
  sudo usermod -aG docker "$USER"
  echo ">> Docker instalado. Cierra la sesión SSH, vuelve a entrar y ejecuta ./deploy.sh otra vez."
  exit 0
fi

if [ ! -f .env.production ]; then
  cp .env.production.example .env.production
  echo ">> Se creó .env.production."
  echo ">> EDITA al menos SECRET_KEY, ALLOWED_HOSTS y POSTGRES_PASSWORD, y vuelve a ejecutar ./deploy.sh"
  echo ">> Genera una SECRET_KEY con: python3 -c \"import secrets; print(secrets.token_urlsafe(50))\""
  exit 0
fi

docker compose -f docker-compose.aws.yml up -d --build

docker compose -f docker-compose.aws.yml exec -T web python manage.py seed_demo || true

echo ""
echo "=============================================================="
echo " Desplegado. Revisa: docker compose -f docker-compose.aws.yml logs -f"
echo " URL: http://$(curl -s ifconfig.me):8000"
echo "=============================================================="
