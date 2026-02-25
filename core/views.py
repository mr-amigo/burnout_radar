from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import MoodEntry, HealthLog
from .forms import Task, RegisterForm, MoodForm, HealthLogForm, TaskForm
from datetime import date
import json


def auth_view(request):
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
        elif form_type is None:
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
@require_POST
def task_add(request):
    data = json.loads(request.body)
    task = Task.objects.create(
        user=request.user,
        title=data['title'],
        date=data['date'],
        start_time=data['start_time'],
        duration=data['duration'],
        priority=data['priority'],
        difficulty=data['difficulty'],
    )
    return JsonResponse({'id': task.id, 'status': 'ok'})


@login_required
def task_list(request):
    date = request.GET.get('date')
    tasks = Task.objects.filter(user=request.user, date=date).values(
        'id', 'title', 'date', 'start_time', 'duration', 'priority', 'difficulty', 'is_completed'
    )
    return JsonResponse({'tasks': list(tasks)})


@login_required
@require_POST
def task_toggle(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.is_completed = not task.is_completed
    task.save()
    return JsonResponse({'is_completed': task.is_completed})


@login_required
@require_POST
def task_delete(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.delete()
    return JsonResponse({'status': 'deleted'})


@login_required
def update_mood_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        today = timezone.now().date()

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

    today_mood = MoodEntry.objects.filter(user=request.user, date=today).first()
    today_health = HealthLog.objects.filter(user=request.user, date=today).first()

    context = {
        'today_mood': today_mood,
        'today_health': today_health,
    }
    return render(request, 'home.html', context)
