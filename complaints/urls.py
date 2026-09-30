from django.urls import path
from . import views

urlpatterns = [
    path('report/', views.report_complaint, name='report_complaint'),
    path('my/', views.my_complaints, name='my_complaints'),
    path('<int:pk>/', views.complaint_detail, name='complaint_detail'),
]
