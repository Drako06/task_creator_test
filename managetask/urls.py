from django.urls import path
from .views import task_view, create_task, task_list, delete_task

urlpatterns = [
    path('task/', task_list, name='task_list'),
    path('task_create/', create_task, name='task_create'),
    path('task_delete/<int:task_id>', delete_task, name='task_delete'),
    path('tasks/', task_view, name='task_view'),
    path('tasks/<int:id>/', task_view, name='task_detail'),
]