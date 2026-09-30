from django import template

from accounts.i18n import tr

register = template.Library()


@register.simple_tag
def t(text):
    return tr(text)