from django.conf import settings
from django.urls import re_path
from django.views.static import serve

from .urls import urlpatterns as _base

# DEBUG is off in production, so serve uploaded photos (/media/...) explicitly.
urlpatterns = list(_base) + [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
