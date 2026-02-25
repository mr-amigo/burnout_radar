from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import MoodEntry, HealthLog


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class MoodForm(forms.ModelForm):
    class Meta:
        model = MoodEntry
        fields = ['mood', 'mental_energy', 'physical_energy']

class HealthLogForm(forms.ModelForm):
    class Meta:
        model = HealthLog
        fields = ['sleep_hours', 'water_ml', 'steps', 'screen_time']
