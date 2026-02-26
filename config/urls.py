from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home_view, name='home'),
    path('login/', views.auth_view, name='login'),
    path('register/', views.auth_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # Tasks
    path('api/tasks/', views.task_list, name='task_list'),
    path('api/tasks/add/', views.task_add, name='task_add'),
    path('api/tasks/<int:task_id>/toggle/',
         views.task_toggle, name='task_toggle'),
    path('api/tasks/<int:task_id>/delete/',
         views.task_delete, name='task_delete'),
    path('api/mood/update/', views.update_mood_api,
         name='update_mood_api'),  # mood
    path('api/health/update/', views.update_health_api,
         name='update_health_api'),  # health
    path('api/reflection/save/', views.save_reflection, name='save_reflection'),
    path('api/insights/', views.ai_insights, name='ai_insights'),
]
