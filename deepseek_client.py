# deepseek_client.py
from dotenv import load_dotenv
import os
from openai import OpenAI
import re, json

load_dotenv()

# Lee tu API key desde .env
API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1"

# Inicializa el cliente
client = OpenAI(
    base_url=BASE_URL,
    api_key=API_KEY
)

def clean_markdown_json(text):
    """
    Extrae el JSON que está entre triple backticks, o devuelve
    todo el texto si no los encuentra.
    """
    # Busca un bloque ```...``` y captura lo que hay dentro
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    # Si no hay triple backticks, asume que todo es JSON
    return text.strip()


def normalizar_por_deepseek(texto_ocr: str) -> dict:
    """
    Envía el texto OCR al modelo deepseek-r1 vía OpenRouter
    y devuelve un dict con los campos ya extraídos.
    """
    # Construye el prompt para pedir la extracción de campos
    prompt = (
        "Extrae de este texto los siguientes campos en formato JSON:\n"
        "Nit, Fecha, Monto, IVA, Número de factura, Establecimiento\n\n"
        f"Texto OCR:\n```\n{texto_ocr}\n```"
    )

    completion = client.chat.completions.create(
        extra_headers={
            "HTTP-Referer": os.getenv("SITE_URL", ""),
            "X-Title": os.getenv("SITE_NAME", ""),
        },
        model="deepseek/deepseek-r1:free",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    respuesta = completion.choices[0].message.content
    json_str = clean_markdown_json(respuesta)

    # Asumimos que `respuesta` es un JSON string, así que lo parseamos.
    try:
        data = json.loads(json_str)
    except Exception as e:
        # Si no es JSON válido, devolvemos vacío para fallback
        print("[ERROR] JSON inválido tras limpiar fences:", json_str)
        raise

    # Mapea las claves del JSON de IA a las que usa tu app
    return {
        "nit":               data.get("Nit", ""),
        "fecha":             data.get("Fecha", ""),
        "monto":             str(data.get("Monto", "")),
        "iva":               str(data.get("IVA", "")),
        "número de factura": data.get("Número de factura", ""),
        "establecimiento":   data.get("Establecimiento", "")
    }
