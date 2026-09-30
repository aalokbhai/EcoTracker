from django.urls import path
from . import collector_views

urlpatterns = [
    path('', collector_views.collector_dashboard, name='collector_dashboard'),
]
