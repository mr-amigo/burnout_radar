from django.db import models
from django.contrib.auth.models import User


class Task(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    date = models.DateField()
    start_time = models.TimeField()
    duration = models.PositiveIntegerField(help_text="Тривалість у хвилинах")
    priority = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES, default='medium')
    difficulty = models.PositiveSmallIntegerField(default=3)  # 1-5
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.date})"


class HealthLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    sleep_hours = models.FloatField(default=0)
    water_ml = models.PositiveIntegerField(default=0)
    steps = models.PositiveIntegerField(default=0)
    screen_time = models.FloatField(
        default=0, help_text="Екранний час у годинах")

    class Meta:
        unique_together = ('user', 'date')

    def __str__(self):
        return f"Health log {self.user} — {self.date}"


class MoodEntry(models.Model):
    MOOD_CHOICES = [
        (1, '😞 Дуже погано'),
        (2, '😕 Погано'),
        (3, '😐 Нейтрально'),
        (4, '🙂 Добре'),
        (5, '😄 Чудово'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    mood = models.PositiveSmallIntegerField(choices=MOOD_CHOICES)
    mental_energy = models.PositiveSmallIntegerField()   # 1-10
    physical_energy = models.PositiveSmallIntegerField()  # 1-10
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'date')

    def __str__(self):
        return f"Mood {self.user} — {self.date}"


class Reflection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'date')

    def __str__(self):
        return f"Reflection {self.user} — {self.date}"
