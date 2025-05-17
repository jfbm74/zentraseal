# documents/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.conf import settings
from .models import Document, Patient, DocumentVerification
from .forms import DocumentUploadForm, PatientForm
from .utils import secure_pdf, verify_document_hash
import os
import random
import string
from datetime import datetime
import uuid


@login_required
def upload_document(request):
    """Vista para subir y asegurar nuevos documentos."""
    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.created_by = request.user
            
            # Generar código de verificación único
            verification_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            document.verification_code = verification_code
            
            document.save()
            
            try:
                # Procesar el PDF para agregar seguridad
                secure_file_path = secure_pdf(
                    document.file.path,
                    document.patient,
                    document.verification_code,
                    request.user
                )
                
                # Verificar que la ruta existe
                if os.path.exists(secure_file_path):
                    # Obtener ruta relativa para guardar en la base de datos
                    rel_path = os.path.relpath(secure_file_path, settings.MEDIA_ROOT)
                    document.secure_file = rel_path
                    document.is_signed = True
                    document.save()
                    messages.success(request, 'Documento protegido exitosamente.')
                    return redirect('document_detail', pk=document.pk)
                else:
                    raise ValueError(f"El archivo seguro no existe: {secure_file_path}")
            except Exception as e:
                print(f"Error al procesar el documento: {str(e)}")
                messages.error(request, f'Error al procesar el documento: {str(e)}')
    else:
        form = DocumentUploadForm()
    
    return render(request, 'documents/upload.html', {'form': form})

@login_required
def document_detail(request, pk):
    """Vista para mostrar los detalles de un documento."""
    document = get_object_or_404(Document, pk=pk)
    
    # Solo el creador o administradores pueden ver el documento
    if document.created_by != request.user and not request.user.is_admin:
        messages.warning(request, 'No tienes permiso para ver este documento.')
        return redirect('dashboard')
    
    # URL para verificación del documento
    verification_url = f"{settings.BASE_URL}/documents/verify/?code={document.verification_code}"
    
    return render(request, 'documents/detail.html', {
        'document': document, 
        'verification_url': verification_url
    })

def verify_document(request):
    """Vista para verificar la autenticidad de un documento."""
    # Si hay un código en la URL, pre-verificamos
    code_from_url = request.GET.get('code')
    if code_from_url:
        try:
            document = Document.objects.get(verification_code=code_from_url)
            
            # Enmascarar información sensible del paciente
            from .utils import mask_name, mask_identification
            masked_patient_name = mask_name(document.patient.name)
            masked_patient_id = mask_identification(document.patient.identification)
            
            # Registrar la verificación
            verification = DocumentVerification(
                document=document,
                verified_by_ip=request.META.get('REMOTE_ADDR', '0.0.0.0')
            )
            verification.save()
            
            # URL para verificación del documento
            verification_url = f"{settings.BASE_URL}/documents/verify/?code={document.verification_code}"
            
            return render(request, 'documents/verification_result.html', {
                'document': document,
                'masked_patient_name': masked_patient_name,
                'masked_patient_id': masked_patient_id,
                'is_valid': True,
                'verification_url': verification_url
            })
        except Document.DoesNotExist:
            return render(request, 'documents/verification_result.html', {
                'is_valid': False
            })
    
    # Verificación manual por formulario
    if request.method == 'POST':
        verification_code = request.POST.get('verification_code')
        if verification_code:
            try:
                document = Document.objects.get(verification_code=verification_code)
                
                # Enmascarar información sensible del paciente
                from .utils import mask_name, mask_identification
                masked_patient_name = mask_name(document.patient.name)
                masked_patient_id = mask_identification(document.patient.identification)
                
                # Registrar la verificación
                verification = DocumentVerification(
                    document=document,
                    verified_by_ip=request.META.get('REMOTE_ADDR', '0.0.0.0')
                )
                verification.save()
                
                # URL para verificación del documento
                verification_url = f"{settings.BASE_URL}/documents/verify/?code={document.verification_code}"
                
                return render(request, 'documents/verification_result.html', {
                    'document': document,
                    'masked_patient_name': masked_patient_name,
                    'masked_patient_id': masked_patient_id,
                    'is_valid': True,
                    'verification_url': verification_url
                })
            except Document.DoesNotExist:
                return render(request, 'documents/verification_result.html', {
                    'is_valid': False
                })
    
    return render(request, 'documents/verify.html')


@login_required
def serve_pdf(request, pk):
    """Vista especializada para servir archivos PDF con las cabeceras correctas."""
    document = get_object_or_404(Document, pk=pk)
    
    # Verificación de permisos
    if document.created_by != request.user and not request.user.is_admin and not request.user.is_staff:
        messages.warning(request, 'No tienes permiso para ver este documento.')
        return redirect('dashboard')
    
    # Verificar que el archivo existe
    if document.secure_file and os.path.exists(document.secure_file.path):
        # Leer el contenido del archivo
        with open(document.secure_file.path, 'rb') as f:
            file_content = f.read()
        
        # Crear respuesta con cabeceras específicas
        response = HttpResponse(file_content, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{os.path.basename(document.secure_file.name)}"'
        
        # Eliminar explícitamente la cabecera X-Frame-Options
        if 'X-Frame-Options' in response:
            del response['X-Frame-Options']
        
        return response
    else:
        messages.error(request, 'El archivo no existe o no se puede acceder a él.')
        return redirect('document_detail', pk=document.pk)
    

@login_required
def verify_document_security(request, pk):
    """Vista para verificar la seguridad de un documento."""
    document = get_object_or_404(Document, pk=pk)
    
    # Verificar permisos
    if document.created_by != request.user and not request.user.is_admin and not request.user.is_staff:
        messages.warning(request, 'No tienes permiso para verificar este documento.')
        return redirect('dashboard')
    
    # Verificar que el archivo existe
    if document.secure_file and os.path.exists(document.secure_file.path):
        from .utils import verify_pdf_protection
        
        # Verificar la seguridad del PDF
        protection_info = verify_pdf_protection(document.secure_file.path)
        
        if protection_info.get("is_protected", False):
            messages.success(
                request, 
                'El documento está protegido correctamente contra ediciones.'
            )
        else:
            error_msg = protection_info.get("error", "Razón desconocida")
            messages.error(
                request, 
                f'El documento no está protegido correctamente: {error_msg}'
            )
    else:
        messages.error(request, 'El archivo no existe o no se puede acceder a él.')
    
    return redirect('document_detail', pk=document.pk)

