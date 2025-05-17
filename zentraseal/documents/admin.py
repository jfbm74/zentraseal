# En accounts/admin.py o donde tengas tu modelo Paciente
from django.contrib import admin
from .models import Patient

admin.site.register(Patient)