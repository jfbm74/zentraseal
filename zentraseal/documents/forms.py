# documents/forms.py
from django import forms
from .models import Document, Patient

class PatientForm(forms.ModelForm):
    """Formulario para crear y editar pacientes."""
    class Meta:
        model = Patient
        fields = ('name', 'identification', 'date_of_birth', 'email', 'phone')
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'name': 'Nombre completo',
            'identification': 'Número de identificación',
            'date_of_birth': 'Fecha de nacimiento',
            'email': 'Correo electrónico',
            'phone': 'Teléfono'
        }

class DocumentUploadForm(forms.ModelForm):
    """Formulario para subir documentos."""
    class Meta:
        model = Document
        fields = ('title', 'document_type', 'file', 'patient')
        widgets = {
            'file': forms.FileInput(attrs={'accept': 'application/pdf'}),
        }
        labels = {
            'title': 'Título del documento',
            'document_type': 'Tipo de documento',
            'file': 'Archivo PDF',
            'patient': 'Paciente'
        }
        
    def clean_file(self):
        """Validación del archivo PDF."""
        file = self.cleaned_data.get('file')
        if file:
            if not file.name.lower().endswith('.pdf'):
                raise forms.ValidationError('Solo se permiten archivos PDF.')
            if file.size > 10 * 1024 * 1024:  # 10MB limit
                raise forms.ValidationError('El archivo no debe superar los 10MB.')
        return file