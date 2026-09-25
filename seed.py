"""
seed.py — Inicializa la estructura de datos de 'prototipos'.
Uso:  python seed.py

Crea:
  - data/
  - data/documentos/
  - data/entregas/
  - data/equipos.json        (lista vacía)
  - data/entregables.json    (lista vacía)
  - data/avisos.json         (con aviso de bienvenida)

Es idempotente: se puede correr varias veces sin borrar nada.
"""
import json
import os

import config


# ============================================================
# Aviso de bienvenida (se siembra la primera vez)
# ============================================================
AVISO_BIENVENIDA = {
    "id": "aviso_bienvenida",
    "titulo": "¡Bienvenidos al registro de proyectos!",
    "contenido": (
        f"Este es el espacio oficial de {config.APP_NOMBRE} para los equipos "
        f"de {config.ESCUELA}.\n\n"
        "Aquí van a:\n"
        "1. Responder un cuestionario que los ayudará a definir su proyecto.\n"
        "2. Registrar su equipo.\n"
        "3. Consultar las fechas límite y los avisos.\n"
        "4. Subir sus evidencias y reportes en PDF.\n\n"
        "Cualquier duda, consulten con su tutor."
    ),
    "fecha": "2026-09-24T00:00:00",
}


# ============================================================
# Utilidades
# ============================================================
def _crear_carpeta(ruta: str) -> bool:
    """Crea la carpeta si no existe. Devuelve True si la creó."""
    if not os.path.exists(ruta):
        os.makedirs(ruta, exist_ok=True)
        return True
    return False


def _crear_json_si_falta(ruta: str, contenido_inicial) -> bool:
    """
    Crea el archivo JSON solo si no existe.
    Devuelve True si lo creó, False si ya existía.
    """
    if os.path.exists(ruta):
        return False
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(contenido_inicial, f, ensure_ascii=False, indent=2)
    return True


# ============================================================
# Función principal
# ============================================================
def inicializar(verbose: bool = True) -> dict:
    """
    Inicializa toda la estructura del proyecto.
    Devuelve un dict con lo que se creó.
    """
    resultado = {
        "carpetas_creadas": [],
        "archivos_creados": [],
    }

    # 1) Carpetas
    for ruta in [config.RUTA_DATA, config.RUTA_DOCUMENTOS, config.RUTA_ENTREGAS]:
        if _crear_carpeta(ruta):
            resultado["carpetas_creadas"].append(ruta)

    # 2) JSON vacíos
    if _crear_json_si_falta(config.ARCHIVO_EQUIPOS, []):
        resultado["archivos_creados"].append(config.ARCHIVO_EQUIPOS)

    if _crear_json_si_falta(config.ARCHIVO_ENTREGABLES, []):
        resultado["archivos_creados"].append(config.ARCHIVO_ENTREGABLES)

    # 3) Avisos (con bienvenida)
    if _crear_json_si_falta(config.ARCHIVO_AVISOS, [AVISO_BIENVENIDA]):
        resultado["archivos_creados"].append(config.ARCHIVO_AVISOS)

    # 4) Verificar que el banco de ideas esté en su lugar
    if not os.path.exists(config.ARCHIVO_BANCO):
        if verbose:
            print(f"⚠️  Falta {config.ARCHIVO_BANCO}. "
                  "Asegúrate de tenerlo en la raíz del proyecto.")
    else:
        resultado["banco_ideas"] = "OK"

    # 5) Reporte final
    if verbose:
        print("=" * 55)
        print(f"  Inicialización de '{config.APP_NOMBRE}' — {config.ESCUELA}")
        print("=" * 55)

        if resultado["carpetas_creadas"]:
            print("📁 Carpetas creadas:")
            for c in resultado["carpetas_creadas"]:
                print(f"   + {c}")
        else:
            print("📁 Carpetas: ya existían todas")

        if resultado["archivos_creados"]:
            print("📄 Archivos creados:")
            for a in resultado["archivos_creados"]:
                print(f"   + {a}")
        else:
            print("📄 Archivos JSON: ya existían todos")

        if resultado.get("banco_ideas") == "OK":
            print(f"✅ Banco de ideas: OK ({config.ARCHIVO_BANCO})")

        print("-" * 55)
        print("Listo. Ahora puedes correr:  streamlit run app.py")

    return resultado


# ============================================================
# Ejecución directa
# ============================================================
if __name__ == "__main__":
    inicializar(verbose=True)