from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import Task, HealthLog, MoodEntry, Reflection
from .forms import RegisterForm, MoodForm, HealthLogForm, TaskForm
from datetime import date, timedelta
import json
from .burnout import calculate_burnout, DailyInput


def auth_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    login_error = None
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
                login_error = 'Invalid username or password'
        elif form_type is None:
            login_form = RegisterForm(request.POST)
            if login_form.is_valid():
                user = login_form.save()
                login(request, user)
                return redirect('home')

    return render(request, 'login.html', {'form': login_form, 'login_error': login_error})

def logout_view(request):
    logout(request)
    return redirect('login')

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

    today_mood = MoodEntry.objects.filter(
        user=request.user, date=today).first()
    today_health = HealthLog.objects.filter(
        user=request.user, date=today).first()

    # Calculate today's burnout index server-side
    tasks_today = Task.objects.filter(user=request.user, date=today)
    total_hours = sum(t.duration for t in tasks_today) / 60 if tasks_today.exists() else 0
    avg_diff = sum(t.difficulty for t in tasks_today) / tasks_today.count() if tasks_today.exists() else 1.0
    tasks_done = tasks_today.filter(is_completed=True).count()

    bi_input = DailyInput(
        mood=today_mood.mood if today_mood else 3.0,
        mental_energy=today_mood.mental_energy if today_mood else 50.0,
        physical_energy=today_mood.physical_energy if today_mood else 50.0,
        sleep_hours=today_health.sleep_hours if today_health else 7.0,
        water_ml=today_health.water_ml if today_health else 1500,
        screen_time=today_health.screen_time if today_health else 4.0,
        steps=today_health.steps if today_health else 5000,
        total_task_hours=total_hours,
        avg_difficulty=avg_diff,
        tasks_total=tasks_today.count(),
        tasks_completed=tasks_done,
    )
    burnout_result = calculate_burnout(bi_input)

    context = {
        'today_mood': today_mood,
        'today_health': today_health,
        'burnout_index': burnout_result.index,
        'burnout_level': burnout_result.level,
    }
    return render(request, 'home.html', context)


@login_required
@require_POST
def save_reflection(request):
    data = json.loads(request.body)
    text = data.get('text', '').strip()
    today = timezone.now().date()
    Reflection.objects.update_or_create(
        user=request.user, date=today,
        defaults={'text': text}
    )
    return JsonResponse({'status': 'ok'})


@login_required
def ai_insights(request):
    today = timezone.now().date()
    insights = []

    try:
        health = HealthLog.objects.get(user=request.user, date=today)

        if health.sleep_hours < 4:
            insights.append({"icon": "😴", "level": "critical",
                "text": f"Critical sleep deficit ({health.sleep_hours:.1f}h). Under 4h is the strongest burnout predictor. Prioritize sleep tonight above everything else."})
        elif health.sleep_hours < 6:
            insights.append({"icon": "🌙", "level": "warning",
                "text": f"Sleep deficit ({health.sleep_hours:.1f}h). You need 7–8h for full recovery. A short nap today can partially help."})
        elif health.sleep_hours >= 7:
            insights.append({"icon": "✅", "level": "good",
                "text": f"Good sleep ({health.sleep_hours:.1f}h). Well-rested people have significantly lower burnout risk."})

        if health.screen_time > 10:
            insights.append({"icon": "📱", "level": "critical",
                "text": f"Very high screen time ({health.screen_time:.1f}h). Above 10h causes mental fatigue and disrupts sleep. Set a hard stop 1h before bed."})
        elif health.screen_time > 6:
            insights.append({"icon": "📱", "level": "warning",
                "text": f"Elevated screen time ({health.screen_time:.1f}h). Try the 20-20-20 rule: every 20 min, look 20 feet away for 20 seconds."})
        elif health.screen_time <= 4:
            insights.append({"icon": "✅", "level": "good",
                "text": f"Healthy screen time ({health.screen_time:.1f}h). Low screen time supports better sleep and focus."})

        if health.steps < 3000:
            insights.append({"icon": "🏃", "level": "warning",
                "text": f"Low movement ({health.steps:,} steps). Even a 20-minute walk significantly reduces exhaustion."})
        elif health.steps >= 8000:
            insights.append({"icon": "✅", "level": "good",
                "text": f"Great movement ({health.steps:,} steps). Regular activity strongly reduces burnout risk."})

        if health.water_ml < 1000:
            insights.append({"icon": "💧", "level": "critical",
                "text": f"Very low hydration ({health.water_ml}ml). Dehydration impairs concentration, mood, and energy. Drink 2 glasses now."})
        elif health.water_ml < 1500:
            insights.append({"icon": "💧", "level": "warning",
                "text": f"Below-optimal hydration ({health.water_ml}ml). Aim for at least 2000ml/day."})
        elif health.water_ml >= 2000:
            insights.append({"icon": "✅", "level": "good",
                "text": f"Well hydrated ({health.water_ml}ml). Good hydration supports focus and mood stability."})

    except HealthLog.DoesNotExist:
        insights.append({"icon": "📊", "level": "info",
            "text": "Log your health data (sleep, hydration, movement) to get personalized daily insights."})

    try:
        mood = MoodEntry.objects.get(user=request.user, date=today)

        if mood.mood <= 2:
            insights.append({"icon": "💙", "level": "warning",
                "text": "Low mood today. Try a 5-minute breathing exercise, a short walk, or talking to someone you trust."})
        elif mood.mood >= 4:
            insights.append({"icon": "😊", "level": "good",
                "text": "Positive mood today — your strongest protection against burnout. Notice what's contributing to it."})

        if mood.mental_energy < 40:
            insights.append({"icon": "🧠", "level": "warning",
                "text": f"Low mental energy ({mood.mental_energy}%). Avoid demanding tasks right now. Rest today to protect tomorrow."})
        elif mood.mental_energy >= 70:
            insights.append({"icon": "⚡", "level": "good",
                "text": f"High mental energy ({mood.mental_energy}%). Good time for your most demanding tasks."})

        if mood.physical_energy < 40:
            insights.append({"icon": "💪", "level": "warning",
                "text": f"Low physical energy ({mood.physical_energy}%). Light stretching or a short walk can help restore it."})

    except MoodEntry.DoesNotExist:
        insights.append({"icon": "💙", "level": "info",
            "text": "Log your mood and energy to get insights tailored to how you feel today."})

    try:
        tasks = list(Task.objects.filter(user=request.user, date=today))
        if tasks:
            total = len(tasks)
            completed = sum(1 for t in tasks if t.is_completed)
            total_hours = sum(t.duration for t in tasks) / 60
            avg_diff = sum(t.difficulty for t in tasks) / total

            if total_hours > 10:
                insights.append({"icon": "⚠️", "level": "critical",
                    "text": f"Extreme workload ({total_hours:.1f}h planned). Major burnout risk. Try to postpone or delegate at least one task."})
            elif total_hours > 7:
                insights.append({"icon": "⚠️", "level": "warning",
                    "text": f"Heavy workload ({total_hours:.1f}h). Take breaks every 90 minutes and protect at least 1h for recovery."})

            if completed < total * 0.5 and avg_diff > 3:
                insights.append({"icon": "📋", "level": "warning",
                    "text": f"{total - completed}/{total} hard tasks still incomplete. Consider breaking them into smaller steps."})
            elif completed == total and total > 0:
                insights.append({"icon": "✅", "level": "good",
                    "text": f"All {total} tasks completed! Great work — this strongly protects against burnout."})
    except Exception:
        pass

    if not insights:
        insights.append({"icon": "✨", "level": "good",
            "text": "All indicators look healthy today. Keep building this momentum."})

    return JsonResponse({"insights": insights})



@login_required
def burnout_today(request):
    today = timezone.now().date()
    today_mood = MoodEntry.objects.filter(user=request.user, date=today).first()
    today_health = HealthLog.objects.filter(user=request.user, date=today).first()
    tasks_today = Task.objects.filter(user=request.user, date=today)
    total_hours = sum(t.duration for t in tasks_today) / 60 if tasks_today.exists() else 0
    avg_diff = sum(t.difficulty for t in tasks_today) / tasks_today.count() if tasks_today.exists() else 1.0
    tasks_done = tasks_today.filter(is_completed=True).count()

    bi_input = DailyInput(
        mood=today_mood.mood if today_mood else 3.0,
        mental_energy=today_mood.mental_energy if today_mood else 50.0,
        physical_energy=today_mood.physical_energy if today_mood else 50.0,
        sleep_hours=today_health.sleep_hours if today_health else 7.0,
        water_ml=today_health.water_ml if today_health else 1500,
        screen_time=today_health.screen_time if today_health else 4.0,
        steps=today_health.steps if today_health else 5000,
        total_task_hours=total_hours,
        avg_difficulty=avg_diff,
        tasks_total=tasks_today.count(),
        tasks_completed=tasks_done,
    )
    result = calculate_burnout(bi_input)
    return JsonResponse({
        'index': result.index,
        'level': result.level,
        'recommendations': result.recommendations,
    })


@login_required
def analytics_data(request):
    today = timezone.now().date()
    labels = []
    burnout_data = []
    workload_data = []
    mood_data = []
    energy_data = []
    sleep_data = []
    movement_data = []

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        labels.append(day.strftime('%a'))  # Mon, Tue...

        # Tasks
        tasks = Task.objects.filter(user=request.user, date=day)
        total_hours = sum(t.duration for t in tasks) / 60 if tasks.exists() else 0
        workload_data.append(round(total_hours, 1))

        # Mood
        try:
            mood = MoodEntry.objects.get(user=request.user, date=day)
            mood_data.append(mood.mood)
            energy_data.append(round((mood.mental_energy + mood.physical_energy) / 2, 1))
        except MoodEntry.DoesNotExist:
            mood_data.append(None)
            energy_data.append(None)

        # Burnout — наукова формула
        try:
            health = HealthLog.objects.get(user=request.user, date=day)
        except HealthLog.DoesNotExist:
            health = None

        try:
            mood_entry = MoodEntry.objects.get(user=request.user, date=day)
        except MoodEntry.DoesNotExist:
            mood_entry = None

        try:
            health = HealthLog.objects.get(user=request.user, date=day)
            sleep_data.append(float(health.sleep_hours))
            movement_data.append(round(health.steps / 100))  # назад в хвилини
        except HealthLog.DoesNotExist:
            sleep_data.append(None)
            movement_data.append(None)

        tasks_day = Task.objects.filter(user=request.user, date=day)
        total_hours = sum(t.duration for t in tasks_day) / 60
        avg_diff = sum(t.difficulty for t in tasks_day) / tasks_day.count() if tasks_day.exists() else 1.0
        tasks_done = tasks_day.filter(is_completed=True).count()

        bi_input = DailyInput(
            mood             = mood_entry.mood            if mood_entry else 3.0,
            mental_energy    = mood_entry.mental_energy   if mood_entry else 50.0,
            physical_energy  = mood_entry.physical_energy if mood_entry else 50.0,
            sleep_hours      = health.sleep_hours         if health else 7.0,
            water_ml         = health.water_ml            if health else 1500,
            screen_time      = health.screen_time         if health else 4.0,
            steps            = health.steps               if health else 5000,
            total_task_hours = total_hours,
            avg_difficulty   = avg_diff,
            tasks_total      = tasks_day.count(),
            tasks_completed  = tasks_done,
        )
        result = calculate_burnout(bi_input)
        burnout_data.append(result.index)

    return JsonResponse({
        'labels': labels,
        'burnout': burnout_data,
        'workload': workload_data,
        'mood': mood_data,
        'energy': energy_data,
        'sleep': sleep_data,
        'movement': movement_data,
    })

@login_required
def weekly_stats(request):
    today = timezone.now().date()
    moods = []
    mental_energies = []
    physical_energies = []
    sleep_list = []
    movement_list = []
    task_counts = {'total': 0, 'completed': 0}
    reflection_days = 0

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        try:
            mood = MoodEntry.objects.get(user=request.user, date=day)
            moods.append(mood.mood)
            mental_energies.append(mood.mental_energy)
            physical_energies.append(mood.physical_energy)
        except MoodEntry.DoesNotExist:
            pass
        try:
            health = HealthLog.objects.get(user=request.user, date=day)
            sleep_list.append(health.sleep_hours)
            movement_list.append(health.steps / 100)
        except HealthLog.DoesNotExist:
            pass

        day_tasks = Task.objects.filter(user=request.user, date=day)
        task_counts['total'] += day_tasks.count()
        task_counts['completed'] += day_tasks.filter(is_completed=True).count()

        if Reflection.objects.filter(user=request.user, date=day).exists():
            reflection_days += 1

    def avg(lst):
        return round(sum(lst) / len(lst), 1) if lst else None

    # Сьогоднішні дані для картки Today's Status
    try:
        tm = MoodEntry.objects.get(user=request.user, date=today)
        today_mood = {
            'mood': tm.mood,
            'mental_energy': tm.mental_energy,
            'physical_energy': tm.physical_energy,
        }
    except MoodEntry.DoesNotExist:
        today_mood = None

    try:
        th = HealthLog.objects.get(user=request.user, date=today)
        today_health = {
            'sleep_hours': th.sleep_hours,
            'steps': th.steps,
        }
    except HealthLog.DoesNotExist:
        today_health = None

    return JsonResponse({
        'avg_mood': avg(moods),
        'avg_mental_energy': avg(mental_energies),
        'avg_physical_energy': avg(physical_energies),
        'avg_sleep': avg(sleep_list),
        'avg_movement': avg(movement_list),
        'tasks_total': task_counts['total'],
        'tasks_completed': task_counts['completed'],
        'reflection_days': reflection_days,
        'today_mood': today_mood,
        'today_health': today_health,
    })
