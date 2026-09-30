from django.urls import path
from . import admin_views

urlpatterns = [
    path('', admin_views.dashboard, name='dashboard'),
    path('complaints/', admin_views.manage_complaints, name='manage_complaints'),
    path('complaints/<int:pk>/update/', admin_views.update_complaint, name='update_complaint'),
    path('pickups/', admin_views.manage_pickups, name='manage_pickups'),
    path('pickups/<int:pk>/update/', admin_views.update_pickup, name='update_pickup'),
]