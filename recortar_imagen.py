"""
recortar_imagen.py — Utilidad de una sola vez.
Recorta la foto del taller a formato banner horizontal y la reduce de peso.
Uso:  python recortar_imagen.py
"""
import os
from PIL import Image

ENTRADA = "assets/taller.jpg"
SALIDA = "assets/taller_banner.jpg"

# Proporción del banner: 4:1 (muy panorámico)
RATIO_ANCHO_ALTO = 3.0
ANCHO_FINAL = 1600

# Punto focal vertical (0.0 = arriba, 1.0 = abajo, 0.5 = centro)
# Si el recorte corta el techo o las mesas, ajusta este número.
FOCO_Y = 0.28


def main():
    if not os.path.exists(ENTRADA):
        print(f"❌ No encontré {ENTRADA}.")
        print("   Asegúrate de haber guardado la foto ahí.")
        return

    img = Image.open(ENTRADA)
    print(f"📷 Original: {img.size[0]}x{img.size[1]} px")

    ancho, alto = img.size
    alto_objetivo = int(ancho / RATIO_ANCHO_ALTO)

    # Recortar según la orientación
    if alto > alto_objetivo:
        offset_y = int((alto - alto_objetivo) * FOCO_Y)
        img = img.crop((0, offset_y, ancho, offset_y + alto_objetivo))
    elif ancho / alto > RATIO_ANCHO_ALTO:
        ancho_objetivo = int(alto * RATIO_ANCHO_ALTO)
        offset_x = (ancho - ancho_objetivo) // 2
        img = img.crop((offset_x, 0, offset_x + ancho_objetivo, alto))

    # Redimensionar
    factor = ANCHO_FINAL / img.size[0]
    alto_final = int(img.size[1] * factor)
    img = img.resize((ANCHO_FINAL, alto_final), Image.LANCZOS)

    img.save(SALIDA, "JPEG", quality=82, optimize=True)

    peso_kb = os.path.getsize(SALIDA) / 1024
    print(f"✅ Banner guardado: {SALIDA}")
    print(f"   Tamaño: {img.size[0]}x{img.size[1]} px")
    print(f"   Peso:   {peso_kb:.0f} KB")


if __name__ == "__main__":
    main()