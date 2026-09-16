"""Settings de desarrollo (local)."""

from .base import *  # noqa: F401,F403
from .base import env

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0", "testserver"]

INTERNAL_IPS = ["127.0.0.1"]

# Email por consola en desarrollo.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
