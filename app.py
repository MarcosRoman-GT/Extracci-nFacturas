from flask import Flask, render_template, request, redirect, url_for, session, send_file
from werkzeug.utils import secure_filename
from PIL import Image
import pytesseract
import os
import re
import uuid
import cv2
import numpy as np
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from deepseek_client import normalizar_por_deepseek

# Ruta de Tesseract en Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Tesseract\tesseract.exe'

# Importación de extractores personalizados por país
from extractores import (
    extraer_factura_guatemala
)

app = Flask(__name__)
app.secret_key = 'clave_secreta_segura'
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'tiff', 'bmp'}

extractores_por_pais = extraer_factura_guatemala

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def preprocess_image(image_path):
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    image = cv2.resize(image, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    image = cv2.GaussianBlur(image, (5, 5), 0)
    _, thresh = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return Image.fromarray(thresh)

def limpiar_texto(texto):
    texto = texto.replace('\n', ' ').replace('\r', ' ')
    texto = re.sub(r'\s{2,}', ' ', texto)
    return texto.strip()

def extraer_regex(texto, patron, group=1):
    matches = re.findall(patron, texto, re.IGNORECASE)
    if matches:
        return matches[0][group - 1].strip() if isinstance(matches[0], tuple) else matches[0].strip()
    return ""

def extraer_datos(texto):
    texto = limpiar_texto(texto)
    print(texto)
    return {
        "fecha": extraer_regex(texto, r"(fecha.{0,10}?[:\s])\s*([\d]{1,2}[/-][\d]{1,2}[/-][\d]{2,4})", group=2),
        "monto": extraer_regex(texto, r"(total\s*a\s*pagar|total|importe)\s*[:\s]*\$?\s*([\d,\.]+)", group=2),
        "establecimiento": extraer_regex(texto, r"(empresa|comercio|raz[oó]n\s*social|establecimiento)[:\s]*(.+?)(?=\s{2,}|\Z)", group=2),
        "nit": extraer_regex(texto, r"(NIT|RUC|RTN|CUIT)[\s:]*([\w-]+)", group=2),
        "iva": extraer_regex(texto, r"(IVA)[\s:]*\$?([\d,\.]+)", group=2),
        "número de factura": extraer_regex(texto, r"(factura(?:\s*n[º°:]?|(?:\s*no\.|#))\s*)([\w\d-]+)", group=2)
    }

def format_field(key, value):
    if key in ["monto", "iva"]:
        try:
            num = float(value.replace(",", "").replace("$", "").strip())
            return f"${num:,.2f}"
        except:
            return value
    return value

def generar_pdf(datos_extraidos, output_path):
    c = canvas.Canvas(output_path, pagesize=letter)
    c.setFont("Helvetica", 12)
    y = 750
    c.drawString(100, y + 30, "Datos Extraídos de la Factura:")
    for key, value in datos_extraidos.items():
        c.drawString(100, y, f"{key.capitalize()}: {format_field(key, value)}")
        y -= 30
    c.save()

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    usuario = request.form['usuario']
    contraseña = request.form['contraseña']
    if usuario == "admin" and contraseña == "1234":
        session['usuario'] = usuario
        return redirect(url_for('dashboard'))
    else:
        return "Usuario o contraseña incorrectos"

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'usuario' not in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST' and (not request.files.get('archivo') or request.files['archivo'].filename == ""):
        # Reconstruye los datos directamente desde los inputs corregidos
        datos_extraidos = request.form.to_dict(flat=True)
        # Recupera el último texto OCR que habías guardado en sesión
        texto_ocr = session.get('last_ocr', '')
        return render_template('dashboard.html', datos=datos_extraidos, texto_ocr=texto_ocr)

    if request.method == 'POST':
        archivo = request.files.get('archivo')
        pais = request.form.get('pais', '').lower()

        if not archivo or not allowed_file(archivo.filename):
            return "Archivo no permitido o faltante", 400

        extractor = extractores_por_pais

        filename = secure_filename(archivo.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        ruta_archivo = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        archivo.save(ruta_archivo)

        try:
            imagen_preprocesada = preprocess_image(ruta_archivo)
            texto = pytesseract.image_to_string(imagen_preprocesada, config='--psm 6')
        except Exception as e:
            return f"Error al procesar la imagen: {e}", 500

        # Guarda el texto OCR en sesión para poder reutilizarlo
        session['last_ocr'] = texto

        # Normalización IA / fallback local
        try:
            datos_norm = normalizar_por_deepseek(texto)
        except Exception as e:
            print(f"[WARN] DeepSeek falló: {e}")
            datos_norm = {}

        if datos_norm and any(datos_norm.values()):
            datos_extraidos = datos_norm
        else:
            datos_extraidos = extractor(texto) if extractor else extraer_datos(texto)

        return render_template('dashboard.html', datos=datos_extraidos, texto_ocr=texto)

    # ----- 3) GET inicial -----
    return render_template('dashboard.html', datos=None, texto_ocr=None)

@app.route('/generar_pdf', methods=['POST'])
def generar_pdf_route():
    # 1) Captura todos los campos que lleguen del formulario:
    datos = request.form.to_dict(flat=True)

    # 2) Genera nombre y ruta para el PDF
    pdf_filename = f"{uuid.uuid4().hex}.pdf"
    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)

    # 3) Llamas a tu función de generación
    generar_pdf(datos, pdf_path)

    # 4) Lo devuelves:
    return send_file(
        pdf_path,
        as_attachment=True,
        download_name="factura.pdf",
        mimetype="application/pdf"
    )

if __name__ == '__main__':
    app.run(debug=True)



