"""
config.py — Constantes globales de la app "prototipos".
Todo lo que se pueda ajustar sin tocar la lógica vive aquí.
"""

# ============================================================
# Identidad de la app
# ============================================================
APP_NOMBRE = "prototipos"
APP_TITULO = "Prototipos — Guía de proyectos de innovación"
ESCUELA = "CBTIS 303"
ICONO = "🚀"

# ============================================================
# Acceso del tutor (TÚ)
# ============================================================
PASSWORD_TUTOR = "cbtis303"   # ← cámbiala cuando quieras

# ============================================================
# GitHub (se completará en el Paso 9)
# ============================================================
GITHUB_REPO = ""      # ej. "tunombre/prototipos"
GITHUB_BRANCH = "main"

# ============================================================
# Rutas locales
# ============================================================
RUTA_DATA = "data"
RUTA_DOCUMENTOS = "data/documentos"   # PDFs públicos (tú)
RUTA_ENTREGAS = "data/entregas"       # PDFs de alumnos

ARCHIVO_EQUIPOS = "data/equipos.json"
ARCHIVO_AVISOS = "data/avisos.json"
ARCHIVO_ENTREGABLES = "data/entregables.json"
ARCHIVO_BANCO = "banco_ideas.json"

# ============================================================
# Reglas de negocio
# ============================================================
DIAS_AMARILLO = 5          # ≤ 5 días para vencer → amarillo
DIAS_ROJO = 0              # vencido → rojo
MAX_PDF_MB = 20            # tamaño máximo por PDF

ETAPAS = ["inicio", "desarrollo", "cierre"]

ETIQUETA_ETAPA = {
    "inicio":     "Inicio · Proponer y planear",
    "desarrollo": "Desarrollo · Construir, probar y corregir",
    "cierre":     "Cierre · Presentación del proyecto",
}

COLORES_SEMAFORO = {
    "verde":    "#28a745",
    "amarillo": "#FFA500",
    "rojo":     "#dc3545",
}