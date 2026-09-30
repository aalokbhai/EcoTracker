"""WSGI entry point for production. Loads the CNN once per worker so the first upload is fast."""
import logging
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_prod')

from django.core.wsgi import get_wsgi_application  # noqa: E402

application = get_wsgi_application()

if os.environ.get('WARM_MODEL', '1') == '1':
    try:
        import torch
        from complaints import ai

        torch.set_num_threads(1)
        with torch.no_grad():
            ai._load_model()(torch.zeros(1, 3, 224, 224))     # first forward pass is the slow one
        logging.getLogger(__name__).info('CNN model warmed up')
    except Exception:
        logging.getLogger(__name__).exception('Model warm-up skipped')
