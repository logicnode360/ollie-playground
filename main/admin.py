from django.contrib import admin
from .models import Question, Notification

admin.site.register(Question)
admin.site.register(Notification)