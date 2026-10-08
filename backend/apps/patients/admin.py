from django.contrib import admin

from .models import Patient, QueueEvent

admin.site.register(Patient)
admin.site.register(QueueEvent)
