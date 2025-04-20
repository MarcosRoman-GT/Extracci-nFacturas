import re

def buscar(texto, patron):
    match = re.search(patron, texto, re.IGNORECASE)
    return match.group(1).strip() if match else ""

def extraer_factura_guatemala(texto):
    return {
        "Nit": buscar(texto, r"NIT[:\s]*([\d-]+)"),
        "Fecha": buscar(texto, r"Fecha[:\s]*([\d/.-]+)"),
        "Monto": buscar(texto, r"Total[:\s]*Q?\s?([\d,\.]+)"),
        "IVA": buscar(texto, r"IVA[:\s]*([\d,\.]+)"),
        "Número de factura": buscar(texto, r"No[°º:]?\s?([\w\d-]+)"),
        "Establecimiento": buscar(texto, r"Establecimiento[:\s]*(.+)")
    }
