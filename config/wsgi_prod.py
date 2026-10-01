"""WSGI entry point for production."""
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_prod')

from django.core.wsgi import get_wsgi_application  # noqa: E402

application = get_wsgi_application()
