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

    context = {
        'today_mood': today_mood,
        'today_health': today_health,
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
            insights.append(
                "😴 You slept less than 4 hours — this is the leading cause of exhaustion. Try to go to bed earlier tonight.")
        elif health.sleep_hours < 6:
            insights.append(
                "🌙 Sleep deficit increases burnout risk. Aim for 7–8 hours per night.")

        if health.screen_time > 8:
            insights.append(
                "📱 Your screen time is significantly above normal. Try a digital detox in the evening.")
        elif health.screen_time > 4:
            insights.append(
                "📱 Screen time is above recommended levels. Try taking breaks every 2 hours.")

        if health.steps < 3000:
            insights.append(
                "🏃 Very little movement today. Even a 15-minute walk can significantly reduce stress.")

        if health.water_ml < 1000:
            insights.append(
                "💧 Critically low water intake. Dehydration worsens focus and mood.")
        elif health.water_ml < 1500:
            insights.append(
                "💧 Not enough water today. Aim for at least 2 liters per day.")

    except HealthLog.DoesNotExist:
        insights.append("📊 Log your health data to get personalized insights.")

    try:
        mood = MoodEntry.objects.get(user=request.user, date=today)

        if mood.mood <= 2:
            insights.append(
                "💙 Your mood is very low today. Try a short gratitude practice or talk to a friend.")

        if mood.mental_energy <= 3:
            insights.append(
                "🧠 Low mental energy. Avoid complex tasks and prioritize rest.")

        if mood.physical_energy <= 3:
            insights.append(
                "⚡ Low physical energy. Light exercise or a short nap might help.")

    except MoodEntry.DoesNotExist:
        insights.append("💙 Log your mood to get personalized insights.")

    try:
        tasks = Task.objects.filter(user=request.user, date=today)
        total = tasks.count()
        completed = tasks.filter(is_completed=True).count()
        if total > 0:
            incomplete_ratio = (total - completed) / total
            if incomplete_ratio > 0.7:
                insights.append(
                    "✅ More than 70% of tasks incomplete. Try breaking them into smaller steps.")
            total_hours = sum(t.duration for t in tasks) / 60
            if total_hours > 8:
                insights.append(
                    "⚠️ Heavy workload today (8+ hours of tasks). Plan breaks every 90 minutes.")
    except:
        pass

    if not insights:
        insights.append(
            "✨ Great day! All indicators are in the normal range. Keep it up!")

    return JsonResponse({'insights': insights})


@login_required
def analytics_data(request):
    today = timezone.now().date()
    labels = []
    burnout_data = []
    workload_data = []
    mood_data = []
    energy_data = []

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        labels.append(day.strftime('%a'))

        task_list = list(Task.objects.filter(user=request.user, date=day))
        total_hours = sum(t.duration for t in task_list) / 60
        workload_data.append(round(total_hours, 1))

        if task_list:
            avg_difficulty = sum(t.difficulty for t in task_list) / len(task_list)
            difficulty_weight = 1.0 + (avg_difficulty - 1) * 0.125
            workload_score = min(35, total_hours * difficulty_weight * 4.5)
            completed_count = sum(1 for t in task_list if t.is_completed)
            task_pressure = 5 if (completed_count / len(task_list) < 0.5 and avg_difficulty > 3) else 0
        else:
            workload_score = 0
            task_pressure = 0

        try:
            health = HealthLog.objects.get(user=request.user, date=day)
            sleep_score = min(42, max(0, 7.5 - health.sleep_hours) * 6)
            screen_score = min(12, max(0, health.screen_time - 6) * 3)
            activity_score = 8 if health.steps < 3000 else (-6 if health.steps >= 7000 else 0)
            if health.water_ml < 1000:
                hydration_score = 5
            elif health.water_ml < 1500:
                hydration_score = 2
            elif health.water_ml >= 2000:
                hydration_score = -3
            else:
                hydration_score = 0
        except HealthLog.DoesNotExist:
            sleep_score = 15
            screen_score = 0
            activity_score = 0
            hydration_score = 0

        try:
            mood_entry = MoodEntry.objects.get(user=request.user, date=day)
            mood_data.append(mood_entry.mood)
            energy_data.append(round((mood_entry.mental_energy + mood_entry.physical_energy) / 2, 1))
            mood_score = (3 - mood_entry.mood) * 8
            mental_score = 10 if mood_entry.mental_energy < 40 else (-8 if mood_entry.mental_energy > 70 else 0)
            physical_score = 6 if mood_entry.physical_energy < 40 else (-4 if mood_entry.physical_energy > 70 else 0)
        except MoodEntry.DoesNotExist:
            mood_data.append(None)
            energy_data.append(None)
            mood_score = 0
            mental_score = 0
            physical_score = 0

        bi = min(100, max(0, round(
            workload_score + task_pressure +
            sleep_score + screen_score + activity_score + hydration_score +
            mood_score + mental_score + physical_score
        )))
        burnout_data.append(bi)

    return JsonResponse({
        'labels': labels,
        'burnout': burnout_data,
        'workload': workload_data,
        'mood': mood_data,
        'energy': energy_data,
    })
