# documents/utils.py
import os
import hashlib
import qrcode
import math
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.colors import Color
from PyPDF2 import PdfReader, PdfWriter
from django.conf import settings
import random
import string
from PIL import Image, ImageDraw
from datetime import datetime
import uuid
import tempfile
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key

def generate_guilloche_pattern(width, height, density=30):
    """Genera un patrón de guilloche (similar a los billetes) como marca de agua."""
    img = Image.new('RGBA', (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Parámetros para crear patrones complejos
    colors = [(0, 128, 255, 15), (0, 204, 102, 15), (153, 51, 255, 15)]
    
    # Crear múltiples patrones de ondas
    for color in colors:
        for i in range(density):
            amplitude = random.randint(20, 100)
            frequency = random.randint(1, 10) / 100
            offset = random.randint(0, height)
            
            points = []
            for x in range(0, width, 2):
                y = int(offset + amplitude * (
                    0.5 * math.sin(x * frequency) + 
                    0.3 * math.sin(x * frequency * 2.1) +
                    0.2 * math.sin(x * frequency * 4.7)
                ))
                points.append((x, y))
            
            if len(points) > 1:
                draw.line(points, fill=color, width=1)
    
    return img

def create_qr_code(data, size=3*cm):
    """Crea un código QR con los datos proporcionados."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()

def calculate_document_hash(file_path):
    """Calcula un hash SHA-256 del documento."""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def secure_pdf(file_path, patient, verification_code, user):
    """
    Aplica medidas de seguridad al PDF:
    1. Agrega marca de agua tipo guilloche
    2. Inserta código QR para verificación
    3. Agrega metadatos de seguridad
    4. Restringe permisos de edición
    5. Calcula y almacena hash del documento
    """
    # Crear un archivo temporal para el PDF procesado
    output_filename = os.path.join(
        settings.MEDIA_ROOT, 
        'secured', 
        f"{uuid.uuid4()}.pdf"
    )
    
    # Asegurar que el directorio exista
    os.makedirs(os.path.dirname(output_filename), exist_ok=True)
    
    # Leer el PDF original
    reader = PdfReader(file_path)
    writer = PdfWriter()
    
    # Variables para la marca de agua
    verification_url = f"{settings.BASE_URL}/documents/verify/?code={verification_code}"
    
    # Procesar cada página
    for i, page in enumerate(reader.pages):
        # Obtener dimensiones de la página
        page_width = float(page.mediabox.width)
        page_height = float(page.mediabox.height)
        
        # Crear página temporal para marca de agua
        packet = BytesIO()
        c = canvas.Canvas(packet, pagesize=(page_width, page_height))
        
        # Dibujar marca de agua tipo guilloche
        watermark_img = generate_guilloche_pattern(int(page_width), int(page_height))
        watermark_buffer = BytesIO()
        watermark_img.save(watermark_buffer, format="PNG")
        watermark_buffer.seek(0)  # Importante: mover al inicio del buffer
        c.drawImage(
            watermark_buffer, 
            0, 0, 
            width=page_width, 
            height=page_height
        )
        
        # Agregar texto de seguridad
        c.setFont("Helvetica", 8)
        c.setFillColor(Color(0, 0, 0, alpha=0.3))
        
        # Texto de microimpresión repetido como fondo de seguridad
        micro_text = f"ZENTRASEAL-DOC-{verification_code} "
        for y in range(0, int(page_height), 20):
            for x in range(0, int(page_width), len(micro_text) * 3):
                c.drawString(x, y, micro_text)
        
        # Agregar información en el pie de página
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(Color(0, 0, 0, alpha=1))
        footer_text = (
            f"Documento seguro de ZentraSeal • Verificación: {verification_code} • "
            f"Paciente: {patient.identification} • Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        )
        c.drawString(30, 30, footer_text)
        
        # Agregar código QR para verificación
        qr_code = create_qr_code(verification_url)  # Esta línea faltaba
        qr_buffer = BytesIO(qr_code)
        c.drawImage(
            qr_buffer, 
            page_width - 3*cm - 20, 
            20, 
            width=3*cm, 
            height=3*cm
        )
        
        c.save()
        
        # Mover al inicio del buffer
        packet.seek(0)
        watermark = PdfReader(packet)
        
        # Combinar la página original con la marca de agua
        watermarked_page = page
        watermarked_page.merge_page(watermark.pages[0])
        writer.add_page(watermarked_page)
    
    # Establecer restricciones de seguridad
    writer.encrypt(
        user_password="",  # No password required to open
        owner_password=f"{patient.identification}{verification_code}",  # Password to modify
        use_128bit=True,
        permissions_flag=4  # Allow only printing
    )
    
    # Guardar el archivo resultante
    with open(output_filename, "wb") as output_file:
        writer.write(output_file)
    
    # Calcular y almacentar el hash del documento
    document_hash = calculate_document_hash(output_filename)
    
    # Aquí se puede implementar el registro en blockchain si es necesario
    
    return output_filename

def verify_document_hash(file_path, stored_hash):
    """Verifica si el hash del documento coincide con el almacenado."""
    current_hash = calculate_document_hash(file_path)
    return current_hash == stored_hash