from django.urls import path
from . import views

urlpatterns = [
    # Сторінки
    path('', views.home_view, name='home'),
    path('login/', views.auth_view, name='login'),
    path('register/', views.auth_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # API — таски
    path('api/tasks/', views.api_tasks, name='api_tasks'),
    path('api/tasks/<int:task_id>/', views.api_task_detail, name='api_task_detail'),

    # API — mood log
    path('api/mood/', views.api_mood, name='api_mood'),

    # API — burnout
    path('api/burnout/', views.api_burnout, name='api_burnout'),
]
