from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from .models import MoodEntry, HealthLog
from .forms import RegisterForm, MoodForm, HealthLogForm
import json
from datetime import date


def auth_view(request):
    """Одна сторінка для логіну і реєстрації"""
    # Якщо вже залогінений — на головну
    if request.user.is_authenticated:
        return redirect('home')

    login_form = None

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'login':
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                return redirect('home')
            else:
                login_form = {'errors': True,
                              'message': 'Невірний логін або пароль'}

        elif form_type is None:  # register form
            form = RegisterForm(request.POST)
            if form.is_valid():
                user = form.save()
                login(request, user)
                return redirect('home')
            else:
                login_form = form

    return render(request, 'login.html', {'form': login_form})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def home_view(request):
    return render(request, 'home.html')


@login_required
def update_mood_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        today = timezone.now().date()

        # update_or_create: шукає за 'defaults', створює/оновлює решту
        obj, created = MoodEntry.objects.update_or_create(
            user=request.user,
            date=today,
            defaults={
                'mood': data.get('mood'),
                'mental_energy': data.get('mental_energy'),
                'physical_energy': data.get('physical_energy')
            }
        )
        return JsonResponse({'status': 'success', 'created': created})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def update_health_api(request):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        today = timezone.now().date()

        # Зберігаємо або оновлюємо дані за сьогодні
        obj, created = HealthLog.objects.update_or_create(
            user=request.user,
            date=today,
            defaults={
                'sleep_hours': data.get('sleep_hours', 0),
                'water_ml': data.get('water_ml', 0),
                'steps': data.get('steps', 0),
                'screen_time': data.get('screen_time', 0),
            }
        )
        return JsonResponse({'status': 'success', 'created': created})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def home_view(request):
    today = date.today()

    # Дістаємо сьогоднішні записи поточного користувача (якщо вони є)
    today_mood = MoodEntry.objects.filter(user=request.user, date=today).first()
    today_health = HealthLog.objects.filter(user=request.user, date=today).first()

    # Передаємо їх у шаблон
    context = {
        'today_mood': today_mood,
        'today_health': today_health,
    }
    return render(request, 'home.html', context)
