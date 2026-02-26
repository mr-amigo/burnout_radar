from django.contrib import admin
from .models import Task, DailyLog

admin.site.register(Task)
admin.site.register(DailyLog)
