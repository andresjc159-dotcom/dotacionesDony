"""Configuración de Celery para Dotaciones Dony."""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery("dotaciones_dony")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
