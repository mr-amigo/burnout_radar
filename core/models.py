from django.db import models
from django.contrib.auth.models import User


class Task(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    user        = models.ForeignKey(User, on_delete=models.CASCADE)
    name        = models.CharField(max_length=255)
    date        = models.DateField()
    time        = models.TimeField()
    duration    = models.FloatField(help_text="Тривалість у годинах")
    priority    = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    difficulty  = models.PositiveSmallIntegerField(default=3)  # 1-5
    done        = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.date})"


class DailyLog(models.Model):
    MOOD_CHOICES = [
        (1, '😞 Very Low'),
        (2, '😕 Low'),
        (3, '😐 Neutral'),
        (4, '🙂 Good'),
        (5, '😄 Great'),
    ]

    user            = models.ForeignKey(User, on_delete=models.CASCADE)
    date            = models.DateField()
    mood            = models.PositiveSmallIntegerField(choices=MOOD_CHOICES)
    mental_energy   = models.PositiveSmallIntegerField()   # 0-100
    physical_energy = models.PositiveSmallIntegerField()   # 0-100
    sleep_hours     = models.FloatField(default=7.0)
    hydration       = models.FloatField(default=6.0)       # склянки
    screen_time     = models.FloatField(default=4.0)       # години
    movement_min    = models.FloatField(default=30.0)      # хвилини
    reflection      = models.TextField(blank=True, default='')
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'date')

    def __str__(self):
        return f"DailyLog {self.user} — {self.date}"
