# documents/models.py
from django.db import models
from django.conf import settings
import uuid
import os
import random



def get_file_path(instance, filename):
    """Genera una ruta única para cada archivo PDF."""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('documents/', filename)

class Patient(models.Model):
    """Modelo para almacenar información de pacientes."""
    name = models.CharField(max_length=100)
    identification = models.CharField(max_length=20, unique=True)
    date_of_birth = models.DateField()
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    
    def __str__(self):
        return f"{self.name} ({self.identification})"

class Document(models.Model):
    """Modelo para almacenar documentos médicos."""
    DOCUMENT_TYPES = (
        ('medical_history', 'Historia Clínica'),
        ('disability', 'Incapacidad'),
        ('prescription', 'Prescripción'),
        ('other', 'Otro'),
    )
    
    title = models.CharField(max_length=200)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    file = models.FileField(upload_to=get_file_path)
    secure_file = models.FileField(upload_to='secured/', null=True, blank=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='documents')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    document_hash = models.CharField(max_length=64, unique=True, blank=True, null=True)
    verification_code = models.CharField(max_length=10, unique=True, blank=True, null=True)
    is_signed = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.title} - {self.patient.name}"
    
    def save(self, *args, **kwargs):
        if not self.verification_code:
            # Generar código de verificación único
            self.verification_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        super().save(*args, **kwargs)

class DocumentVerification(models.Model):
    """Modelo para llevar registro de verificaciones de documentos."""
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='verifications')
    verified_at = models.DateTimeField(auto_now_add=True)
    verified_by_ip = models.GenericIPAddressField()
    is_valid = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Verificación: {self.document.title} - {self.verified_at}"