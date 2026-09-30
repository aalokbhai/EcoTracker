from django.utils import translation

from .translations import HI


def tr(text):
    """Return the Hindi version when Hindi is active, otherwise the same text."""
    text = str(text)
    if translation.get_language() == 'hi':
        return HI.get(text, text)
    return text