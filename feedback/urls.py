from django.urls import path
from . import views

urlpatterns = [
    path('', views.feedback_list, name='feedback'),
    path('<int:pk>/reply/', views.add_reply, name='feedback_reply'),
]
