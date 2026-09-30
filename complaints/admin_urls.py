from django.urls import path
from . import admin_views

urlpatterns = [
    path('', admin_views.dashboard, name='dashboard'),
    path('complaints/', admin_views.manage_complaints, name='manage_complaints'),
    path('pickups/', admin_views.manage_pickups, name='manage_pickups'),
    path('collectors/', admin_views.manage_collectors, name='manage_collectors'),
    path('collectors/<int:pk>/approval/', admin_views.set_collector_approval, name='set_collector_approval'),
]
