import json
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from .models import Task, DailyLog
from .burnout import calculate_burnout, DailyInput


# ── СТОРІНКИ ─────────────────────────────────────────────────

def auth_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    form = None

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
                form = {'errors': True}

        else:  # register
            form = UserCreationForm(request.POST)
            if form.is_valid():
                user = form.save()
                login(request, user)
                return redirect('home')

    return render(request, 'core/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def home_view(request):
    return render(request, 'core/home.html')


# ── API TASKS ─────────────────────────────────────────────────

@login_required
@require_http_methods(["GET", "POST"])
def api_tasks(request):
    if request.method == 'GET':
        date = request.GET.get('date')
        tasks = Task.objects.filter(user=request.user)
        if date:
            tasks = tasks.filter(date=date)
        data = [{
            'id':         t.id,
            'name':       t.name,
            'date':       str(t.date),
            'time':       str(t.time)[:5],
            'duration':   t.duration,
            'priority':   t.priority,
            'difficulty': t.difficulty,
            'done':       t.done,
        } for t in tasks]
        return JsonResponse({'tasks': data})

    if request.method == 'POST':
        body = json.loads(request.body)
        task = Task.objects.create(
            user       = request.user,
            name       = body['name'],
            date       = body['date'],
            time       = body.get('time', '09:00'),
            duration   = body.get('duration', 1),
            priority   = body.get('priority', 'medium'),
            difficulty = body.get('difficulty', 3),
            done       = body.get('done', False),
        )
        return JsonResponse({'id': task.id, 'status': 'created'})


@login_required
@require_http_methods(["PATCH", "DELETE"])
def api_task_detail(request, task_id):
    try:
        task = Task.objects.get(id=task_id, user=request.user)
    except Task.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)

    if request.method == 'PATCH':
        body = json.loads(request.body)
        if 'done' in body:
            task.done = body['done']
        task.save()
        return JsonResponse({'status': 'updated'})

    if request.method == 'DELETE':
        task.delete()
        return JsonResponse({'status': 'deleted'})


# ── API MOOD ──────────────────────────────────────────────────

@login_required
@require_http_methods(["GET", "POST"])
def api_mood(request):
    if request.method == 'GET':
        date = request.GET.get('date')
        logs = DailyLog.objects.filter(user=request.user)
        if date:
            logs = logs.filter(date=date)
        data = [{
            'date':            str(l.date),
            'mood':            l.mood,
            'mental':          l.mental_energy,
            'physical':        l.physical_energy,
            'sleep':           l.sleep_hours,
            'hydration':       l.hydration,
            'screenTime':      l.screen_time,
            'movement':        l.movement_min,
            'reflection':      l.reflection,
        } for l in logs]
        return JsonResponse({'logs': data})

    if request.method == 'POST':
        body = json.loads(request.body)
        log, _ = DailyLog.objects.update_or_create(
            user=request.user,
            date=body['date'],
            defaults={
                'mood':            body.get('mood', 3),
                'mental_energy':   body.get('mental', 50),
                'physical_energy': body.get('physical', 50),
                'sleep_hours':     body.get('sleep', 7),
                'hydration':       body.get('hydration', 6),
                'screen_time':     body.get('screenTime', 4),
                'movement_min':    body.get('movement', 30),
                'reflection':      body.get('reflection', ''),
            }
        )
        return JsonResponse({'status': 'saved'})


# ── API BURNOUT ───────────────────────────────────────────────

@login_required
@require_http_methods(["GET"])
def api_burnout(request):
    date = request.GET.get('date')
    if not date:
        return JsonResponse({'error': 'date required'}, status=400)

    tasks = Task.objects.filter(user=request.user, date=date)
    try:
        log = DailyLog.objects.get(user=request.user, date=date)
    except DailyLog.DoesNotExist:
        log = None

    total_hours  = sum(t.duration for t in tasks)
    avg_diff     = sum(t.difficulty for t in tasks) / len(tasks) if tasks else 1.0
    tasks_done   = tasks.filter(done=True).count()

    data = DailyInput(
        mood             = log.mood            if log else 3.0,
        mental_energy    = log.mental_energy   if log else 50.0,
        physical_energy  = log.physical_energy if log else 50.0,
        sleep_hours      = log.sleep_hours     if log else 7.0,
        hydration        = log.hydration       if log else 6.0,
        screen_time      = log.screen_time     if log else 4.0,
        movement_min     = log.movement_min    if log else 30.0,
        total_task_hours = total_hours,
        avg_difficulty   = avg_diff,
        tasks_total      = tasks.count(),
        tasks_completed  = tasks_done,
    )

    result = calculate_burnout(data)

    return JsonResponse({
        'index':           result.index,
        'level':           result.level,
        'components':      result.components,
        'recommendations': result.recommendations,
    })
