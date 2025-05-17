# documents/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_document, name='upload_document'),
    path('detail/<int:pk>/', views.document_detail, name='document_detail'),
    path('verify/', views.verify_document, name='verify_document'),
]