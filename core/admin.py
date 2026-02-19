from django.contrib import admin
from .models import Task, HealthLog, MoodEntry, Reflection

admin.site.register(Task)
admin.site.register(HealthLog)
admin.site.register(MoodEntry)
admin.site.register(Reflection)
