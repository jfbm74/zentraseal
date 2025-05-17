# accounts/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    """Modelo de usuario extendido para funcionalidades adicionales"""
    is_doctor = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    signature_image = models.ImageField(upload_to='signatures/', null=True, blank=True)
    organization = models.CharField(max_length=100, default="Bonsana")
    
    def __str__(self):
        return self.username

