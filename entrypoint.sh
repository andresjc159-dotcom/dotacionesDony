#!/bin/sh
set -e

echo "Aplicando migraciones..."
python manage.py migrate --settings=config.settings.prod

echo "Recolectando archivos estáticos..."
python manage.py collectstatic --noinput --settings=config.settings.prod

echo "Iniciando gunicorn..."
exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-8000}"
