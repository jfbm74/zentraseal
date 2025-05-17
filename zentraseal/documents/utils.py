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





def generate_guilloche_pattern(width, height):
    """
    Genera un patrón guilloche profesional con alta densidad de líneas basado en 
    cuadrículas de flujo distorsionadas, similar a documentos de seguridad premium.
    """
    img = Image.new('RGBA', (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Colores sutiles en tonos verde, azul y gris
    colors = [
        (0, 150, 100, 25),    # Verde esmeralda
        (100, 150, 200, 25),  # Azul cielo
        (100, 100, 100, 20),  # Gris
        (80, 160, 120, 22)    # Verde-azulado
    ]
    
    # Parámetros de distorsión
    freq_x = random.uniform(0.005, 0.012)
    freq_y = random.uniform(0.005, 0.012)
    amp_x = random.uniform(15, 25)
    amp_y = random.uniform(15, 25)
    
    phase_x = random.uniform(0, 2 * math.pi)
    phase_y = random.uniform(0, 2 * math.pi)
    
    # Reducir el espaciado para aumentar la densidad de líneas
    spacing_primary = 8    # Líneas principales (antes 15)
    spacing_secondary = 16  # Líneas secundarias
    
    # 1. LÍNEAS HORIZONTALES PRINCIPALES (MAYOR DENSIDAD)
    for y_base in range(0, height, spacing_primary):
        color = colors[0]  # Verde para líneas horizontales
        points = []
        
        for x in range(0, width + 1, 2):
            # Aplicar distorsión sinusoidal
            distort_y = amp_y * math.sin(x * freq_x + y_base * freq_y + phase_x)
            y = y_base + distort_y
            
            if 0 <= y < height:
                points.append((x, y))
        
        if len(points) > 1:
            draw.line(points, fill=color, width=1)
    
    # 2. LÍNEAS VERTICALES PRINCIPALES (MAYOR DENSIDAD)
    for x_base in range(0, width, spacing_primary):
        color = colors[1]  # Azul para líneas verticales
        points = []
        
        for y in range(0, height + 1, 2):
            # Distorsión diferente para crear efecto de flujo
            distort_x = amp_x * math.sin(y * freq_y + x_base * freq_x + phase_y)
            x = x_base + distort_x
            
            if 0 <= x < width:
                points.append((x, y))
        
        if len(points) > 1:
            draw.line(points, fill=color, width=1)
    
    # 3. LÍNEAS DIAGONALES TIPO "/"
    for d_base in range(-height, width, spacing_secondary):
        color = colors[2]  # Gris para diagonales
        points = []
        
        for t in range(0, width + height, 4):
            x_base = d_base + t
            y_base = t
            
            # Distorsión combinada
            distort_x = amp_x * 0.7 * math.sin(y_base * freq_y + phase_x)
            distort_y = amp_y * 0.7 * math.sin(x_base * freq_x + phase_y)
            
            x = x_base + distort_x
            y = y_base + distort_y
            
            if 0 <= x < width and 0 <= y < height:
                points.append((x, y))
        
        if len(points) > 1:
            draw.line(points, fill=color, width=1)
    
    # 4. LÍNEAS DIAGONALES TIPO "\"
    for d_base in range(-height, width, spacing_secondary):
        color = colors[3]  # Verde-azulado para diagonales inversas
        points = []
        
        for t in range(0, width + height, 4):
            x_base = d_base + t
            y_base = height - t
            
            # Distorsión combinada con fase diferente
            distort_x = amp_x * 0.7 * math.sin(y_base * freq_y + phase_x + math.pi/2)
            distort_y = amp_y * 0.7 * math.sin(x_base * freq_x + phase_y + math.pi/2)
            
            x = x_base + distort_x
            y = y_base + distort_y
            
            if 0 <= x < width and 0 <= y < height:
                points.append((x, y))
        
        if len(points) > 1:
            draw.line(points, fill=color, width=1)
    
    # 5. LÍNEAS HORIZONTALES SECUNDARIAS (INTERCALADAS)
    for y_base in range(spacing_primary // 2, height, spacing_primary):
        color = (colors[0][0], colors[0][1], colors[0][2], colors[0][3] - 5)  # Verde más transparente
        points = []
        
        for x in range(0, width + 1, 2):
            # Aplicar distorsión sinusoidal con fase ligeramente diferente
            distort_y = amp_y * math.sin(x * freq_x + y_base * freq_y + phase_x + math.pi/4)
            y = y_base + distort_y
            
            if 0 <= y < height:
                points.append((x, y))
        
        if len(points) > 1:
            draw.line(points, fill=color, width=1)
    
    # 6. LÍNEAS VERTICALES SECUNDARIAS (INTERCALADAS)
    for x_base in range(spacing_primary // 2, width, spacing_primary):
        color = (colors[1][0], colors[1][1], colors[1][2], colors[1][3] - 5)  # Azul más transparente
        points = []
        
        for y in range(0, height + 1, 2):
            # Distorsión con fase ligeramente diferente
            distort_x = amp_x * math.sin(y * freq_y + x_base * freq_x + phase_y + math.pi/4)
            x = x_base + distort_x
            
            if 0 <= x < width:
                points.append((x, y))
        
        if len(points) > 1:
            draw.line(points, fill=color, width=1)
    
    # 7. EFECTO DE CAMPO DE FLUJO CENTRAL CON MAYOR DENSIDAD
    # Crear distorsión adicional en el centro para el efecto de "remolino"
    center_x, center_y = width / 2, height / 2
    radius = min(width, height) * 0.4
    
    # Patrones radiales (más densidad)
    for angle in range(0, 360, 5):  # Cada 5 grados en lugar de 10
        rad = math.radians(angle)
        color = random.choice(colors)
        points = []
        
        for r in range(0, int(radius), 5):  # Saltos de 5 unidades en lugar de 10
            # Calcular posición base
            x_base = center_x + r * math.cos(rad)
            y_base = center_y + r * math.sin(rad)
            
            # Distorsión radial
            x = x_base + amp_x * 0.3 * math.sin(r * freq_x * 2 + phase_x)
            y = y_base + amp_y * 0.3 * math.sin(r * freq_y * 2 + phase_y)
            
            if 0 <= x < width and 0 <= y < height:
                points.append((x, y))
        
        if len(points) > 1:
            draw.line(points, fill=color, width=1)
    
    # 8. PATRONES CONCÉNTRICOS ADICIONALES
    for r_base in range(20, int(radius), 30):
        color = random.choice(colors)
        points = []
        
        for angle in range(0, 360, 2):
            rad = math.radians(angle)
            
            # Radius con ondulación
            r = r_base + 5 * math.sin(8 * rad)
            
            x = center_x + r * math.cos(rad)
            y = center_y + r * math.sin(rad)
            
            if 0 <= x < width and 0 <= y < height:
                points.append((x, y))
        
        # Cerrar el círculo
        if points and len(points) > 2:
            points.append(points[0])
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
    return img  # Retornamos la imagen directamente, no bytes

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
    2. Agrega marca de agua de imagen repetida (logo)
    3. Inserta código QR para verificación
    4. Agrega metadatos de seguridad
    5. Restringe permisos de edición
    6. Calcula y almacena hash del documento
    """
    # Importaciones
    from .utils import mask_identification, verify_pdf_protection
    
    # Crear un archivo temporal para el PDF procesado
    output_filename = os.path.join(
        settings.MEDIA_ROOT, 
        'secured', 
        f"{uuid.uuid4()}.pdf"
    )
    
    # Asegurar que el directorio exista
    os.makedirs(os.path.dirname(output_filename), exist_ok=True)
    
    # Configurar directorio de marcas de agua si no existe
    watermarks_dir = os.path.join(settings.MEDIA_ROOT, 'watermarks')
    os.makedirs(watermarks_dir, exist_ok=True)
    
    # Ruta a la imagen de marca de agua (logo)
    watermark_image_path = os.path.join(watermarks_dir, 'logo.png')
    
    # Texto para microimpresión
    micro_text = " "

    # Enmascarar ID del paciente para el pie de página
    masked_patient_id = mask_identification(patient.identification)

    # Crear un directorio temporal para guardar imágenes temporales
    temp_dir = tempfile.mkdtemp()
    
    try:
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
            
            # 1. Dibujar marca de agua tipo guilloche
            watermark_img = generate_guilloche_pattern(int(page_width), int(page_height))
            watermark_path = os.path.join(temp_dir, f"watermark_{i}.png")
            watermark_img.save(watermark_path)
            
            # Aplicar el patrón guilloche
            c.drawImage(
                watermark_path, 
                0, 0, 
                width=page_width, 
                height=page_height,
                mask='auto', 
                preserveAspectRatio=True
            )
            
            # 2. Agregar marca de agua de imagen repetida (logo)
            # 2. Agregar marca de agua de imagen repetida (logo)
            if os.path.exists(watermark_image_path):
                # Tamaño de la imagen de marca de agua (reducido para mayor densidad)
                wm_width = 120  # Reducido de 150
                wm_height = 80  # Reducido de 100
                
                # Espaciado entre imágenes (reducido para mayor repetición)
                x_spacing = 180  # Reducido de 300
                y_spacing = 180  # Reducido de 300
                
                # Rotación aleatoria para cada imagen
                import random
                
                # Configurar transparencia para la marca de agua
                c.saveState()
                c.setFillAlpha(0.07)  # Mantener la misma opacidad para no afectar la legibilidad
                
                # Repetir la imagen por toda la página con un patrón escalonado
                for y in range(30, int(page_height), y_spacing):
                    offset = 90 if (y // y_spacing) % 2 == 0 else 0
                    for x in range(offset, int(page_width), x_spacing):
                        # Rotación aleatoria sutil para variación
                        rotation = random.uniform(-5, 5)
                        
                        c.saveState()
                        c.translate(x + wm_width/2, y + wm_height/2)
                        c.rotate(rotation)
                        c.translate(-wm_width/2, -wm_height/2)
                        
                        c.drawImage(
                            watermark_image_path,
                            0, 0,
                            width=wm_width,
                            height=wm_height,
                            mask='auto',
                            preserveAspectRatio=True
                        )
                        
                        c.restoreState()
            
                c.restoreState()
            
            # 3. Agregar texto de microimpresión de seguridad
            c.setFont("Helvetica", 6)  # Fuente más pequeña
            c.setFillColor(Color(0, 0, 0, alpha=0.08))  # Muy transparente
            
            # Texto de microimpresión repetido como fondo de seguridad
            for y in range(0, int(page_height), 60):  # Espaciado vertical
                for x in range(0, int(page_width), len(micro_text) * 10):  # Espaciado horizontal
                    c.drawString(x, y, micro_text)
            
            # 4. Agregar información en el pie de página con identificación enmascarada
            c.setFont("Helvetica-Bold", 10)
            c.setFillColor(Color(0, 0, 0, alpha=1))
            footer_text = (
                f"Documento seguro de ZentraSeal • Verificación: {verification_code} • "
                f"Paciente: {masked_patient_id} • Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            )
            c.drawString(30, 30, footer_text)
            
            # 5. Crear y guardar el código QR
            qr_img = create_qr_code(verification_url)
            qr_path = os.path.join(temp_dir, f"qr_{i}.png")
            qr_img.save(qr_path)
            
            # Usar la ruta del archivo temporal del QR
            c.drawImage(
                qr_path, 
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
        
        # 6. Establecer restricciones de seguridad
        writer.encrypt(
            user_password="",  # No requiere contraseña para abrir
            owner_password=f"{patient.identification}{verification_code}",  # Contraseña para modificar
            use_128bit=True,
            permissions_flag=4  # Permitir solo impresión
        )
        
        # 7. Guardar el archivo resultante
        with open(output_filename, "wb") as output_file:
            writer.write(output_file)
        
        # 8. Verificar que el PDF esté correctamente protegido
        protection_info = verify_pdf_protection(output_filename)
        if not protection_info.get("is_protected", False):
            print(f"ADVERTENCIA: El PDF no está protegido correctamente: {protection_info}")
            # Aquí podrías lanzar una excepción o manejar el error
        else:
            print(f"PDF protegido correctamente: {protection_info}")
        
        # 9. Calcular el hash del documento
        document_hash = calculate_document_hash(output_filename)
        
        return output_filename
    
    finally:
        # Limpiar los archivos temporales
        import shutil
        try:
            shutil.rmtree(temp_dir)
        except:
            pass


def verify_document_hash(file_path, stored_hash):
    """Verifica si el hash del documento coincide con el almacenado."""
    current_hash = calculate_document_hash(file_path)
    return current_hash == stored_hash


def mask_name(name):
    """
    Enmascara un nombre mostrando solo las primeras 2 letras de cada parte del nombre.
    Ejemplo: "JUAN FELIPE" -> "JU** FE****"
    """
    if not name:
        return ""
        
    masked_parts = []
    parts = name.split()
    
    for part in parts:
        if len(part) <= 2:
            masked_part = part
        else:
            visible_chars = 2
            masked_part = part[:visible_chars] + '*' * (len(part) - visible_chars)
        masked_parts.append(masked_part)
    
    return " ".join(masked_parts)

def mask_identification(identification):
    """
    Enmascara un número de identificación mostrando solo los últimos 4 dígitos.
    Ejemplo: "9979797" -> "***9797"
    """
    if not identification:
        return ""
        
    if len(identification) <= 4:
        return identification
    
    visible_chars = 4
    return '*' * (len(identification) - visible_chars) + identification[-visible_chars:]


def verify_pdf_protection(pdf_path):
    """
    Verifica si un PDF tiene protección contra ediciones.
    
    Args:
        pdf_path: Ruta al archivo PDF.
    
    Returns:
        dict: Un diccionario con el estado de protección del PDF.
    """
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(pdf_path)
        
        # Verificar si el documento está encriptado
        is_encrypted = reader.is_encrypted
        
        # Información sobre permisos (si está disponible)
        permissions = {}
        if is_encrypted:
            # Intentar determinar qué permisos están restringidos
            # Nota: No podemos obtener los permisos exactos sin la contraseña del propietario
            permissions = {
                "is_print_restricted": not reader.can_print,
                "is_modification_restricted": not reader.can_modify,
                "is_extraction_restricted": not reader.can_extract_content,
                "is_annotation_restricted": not reader.can_modify_annotations
            }
        
        return {
            "is_protected": is_encrypted,
            "permissions": permissions
        }
    except Exception as e:
        return {
            "is_protected": False,
            "error": str(e)
        }
    

