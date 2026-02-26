from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Task, MoodEntry, HealthLog
from .models import Reflection


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'date', 'start_time',
                  'duration', 'priority', 'difficulty']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
        }


class MoodForm(forms.ModelForm):
    class Meta:
        model = MoodEntry
        fields = ['mood', 'mental_energy', 'physical_energy']


class HealthLogForm(forms.ModelForm):
    class Meta:
        model = HealthLog
        fields = ['sleep_hours', 'water_ml', 'steps', 'screen_time']


class ReflectionForm(forms.ModelForm):
    class Meta:
        model = Reflection
        fields = ['text']
