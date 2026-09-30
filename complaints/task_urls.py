from django.urls import path
from . import task_views as v

urlpatterns = [
    path('<str:kind>/<int:pk>/approve/', v.task_approve, name='task_approve'),
    path('<str:kind>/<int:pk>/reject/', v.task_reject, name='task_reject'),
    path('<str:kind>/<int:pk>/assign/', v.task_assign, name='task_assign'),
    path('<str:kind>/<int:pk>/verify/', v.task_verify, name='task_verify'),
    path('<str:kind>/<int:pk>/redo/', v.task_redo, name='task_redo'),
    path('<str:kind>/<int:pk>/accept/', v.task_accept, name='task_accept'),
    path('<str:kind>/<int:pk>/clean/', v.task_clean, name='task_clean'),
    path('<str:kind>/<int:pk>/cancel/', v.task_cancel, name='task_cancel'),
]
