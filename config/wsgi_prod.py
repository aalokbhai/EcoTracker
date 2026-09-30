"""WSGI entry point for production. Loads the CNN at start-up so the first upload is fast."""
import logging
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_prod')

from django.core.wsgi import get_wsgi_application  # noqa: E402

application = get_wsgi_application()

if os.environ.get('WARM_MODEL', '1') == '1':
    try:
        from complaints import ai

        ai.warm_up()
        logging.getLogger(__name__).info('CNN model warmed up')
    except Exception:
        logging.getLogger(__name__).exception('Model warm-up skipped')
