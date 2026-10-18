"""
generar_qr.py — Genera el código QR de la app 'prototipos'.
Uso:  python generar_qr.py
Salida: qr_prototipos.png
"""
import qrcode

# ------------------------------------------------------------
# 1) Configuración
# ------------------------------------------------------------
URL_APP = "https://prototipos-cbtis303.streamlit.app"
ARCHIVO_SALIDA = "qr_prototipos.png"


# ------------------------------------------------------------
# 2) Generar el código QR
# ------------------------------------------------------------
qr = qrcode.QRCode(
    version=None,       # Streamlit ajusta el tamaño automáticamente
    error_correction=qrcode.constants.ERROR_CORRECT_M,
    box_size=12,        # Tamaño de cada "cuadrito" del QR (más grande = más px)
    border=3,           # Margen blanco alrededor (en cuadritos)
)

qr.add_data(URL_APP)
qr.make(fit=True)

# ------------------------------------------------------------
# 3) Convertirlo a imagen y guardarlo
# ------------------------------------------------------------
img = qr.make_image(fill_color="black", back_color="white")
img.save(ARCHIVO_SALIDA)

print(f"¡Listo! Se generó '{ARCHIVO_SALIDA}'")
print(f"Contenido: {URL_APP}")