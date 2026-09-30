"""Production settings (Render free web service / any host that runs gunicorn).
Local development keeps using config.settings - nothing in the normal setup changes.

Environment variables (all optional):
  DJANGO_SECRET_KEY   secret key  (set it as a Space *secret*)
  DJANGO_DEBUG        "1" to turn DEBUG on
  ALLOWED_HOSTS       extra hosts, comma separated
  CSRF_TRUSTED        extra trusted origins, comma separated (https://...)
  INSECURE_COOKIES    "1" only when testing over plain http
"""
import os

from .settings import *  # noqa: F401,F403
from .settings import BASE_DIR, MIDDLEWARE, SECRET_KEY as _DEV_KEY

DEBUG = os.environ.get('DJANGO_DEBUG') == '1'
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY') or _DEV_KEY


def _csv(name):
    return [x.strip() for x in os.environ.get(name, '').split(',') if x.strip()]


ALLOWED_HOSTS = ['.onrender.com', 'localhost', '127.0.0.1', '[::1]'] + _csv('ALLOWED_HOSTS')
CSRF_TRUSTED_ORIGINS = ['https://*.onrender.com'] + _csv('CSRF_TRUSTED')
if os.environ.get('RENDER_EXTERNAL_HOSTNAME'):            # set automatically by Render
    ALLOWED_HOSTS.append(os.environ['RENDER_EXTERNAL_HOSTNAME'])
    CSRF_TRUSTED_ORIGINS.append('https://' + os.environ['RENDER_EXTERNAL_HOSTNAME'])

# The platform terminates HTTPS and forwards the original scheme.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

_secure = os.environ.get('INSECURE_COOKIES') != '1'
SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = _secure

# WhiteNoise serves the static files straight from gunicorn (fast, no nginx needed).
MIDDLEWARE = list(MIDDLEWARE)
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage'},
}

# Uploaded photos are served by config.urls_prod
ROOT_URLCONF = 'config.urls_prod'

LOGGING = {
    'version': 1, 'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'root': {'handlers': ['console'], 'level': 'INFO'},
}

# Emails are only printed to the log (no SMTP configured); silence the dev-only-backend warning.
SILENCED_SYSTEM_CHECKS = ['mail.E001']
