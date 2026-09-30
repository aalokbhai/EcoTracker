from django.conf import settings
from django.http import HttpResponse
from django.urls import path, re_path
from django.views.static import serve

from .urls import urlpatterns as _base

# DEBUG is off in production, so serve uploaded photos (/media/...) explicitly.
# /healthz is a cheap URL for Render's health check and for the uptime pinger.
urlpatterns = list(_base) + [
    path('healthz', lambda request: HttpResponse('ok', content_type='text/plain')),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
