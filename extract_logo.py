import cv2
import numpy as np

def extract_logo(image_path: str, output_path: str,
                 header_frac: float = 0.3,
                 min_area_frac: float = 0.001) -> bool:
    """
    Extrae el logo de la parte superior de una factura.
    - header_frac: fracción de la altura total que define la zona superior (p.ej. 0.2 = 20%).
    - min_area_frac: área mínima relativa al área del header para considerar un contorno.
    """
    # Leer la imagen
    img = cv2.imread(image_path)
    if img is None:
        return False

    h, w = img.shape[:2]
    header_h = int(h * header_frac)

    # 1) Recortar solo la cabecera de la factura
    header = img[0:header_h, :]
    gray = cv2.cvtColor(header, cv2.COLOR_BGR2GRAY)

    # 2) Binarizar e invertir para destacar logos oscuros
    _, thresh = cv2.threshold(gray, 0, 255,
                              cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # 3) Morfología de cierre para unir texto y gráficos
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)

    # 4) Encontrar contornos en la cabecera
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)
    candidates = []
    total_area = header_h * w

    for cnt in contours:
        x, y, cw, ch = cv2.boundingRect(cnt)
        area = cw * ch
        # Filtrar por área mínima y NO abarcar casi todo el ancho
        if area > total_area * min_area_frac and cw < w * 0.8:
            candidates.append((x, y, cw, ch, area))

    if not candidates:
        return False

    # 5) Ordenar candidatos: primero mayor área, luego menor y (más arriba)
    candidates.sort(key=lambda c: (-c[4], c[1]))
    x, y, cw, ch, _ = candidates[0]

    # 6) Recortar del header y guardar
    logo_crop = header[y:y+ch, x:x+cw]
    cv2.imwrite(output_path, logo_crop)
    return True

