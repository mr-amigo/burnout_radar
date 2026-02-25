from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home_view, name='home'),
    path('login/', views.auth_view, name='login'),
    path('register/', views.auth_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
]
