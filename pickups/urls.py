from django.urls import path
from . import views

urlpatterns = [
    path('request/', views.request_pickup, name='request_pickup'),
    path('my/', views.my_pickups, name='my_pickups'),
    path('<int:pk>/', views.pickup_detail, name='pickup_detail'),
]
