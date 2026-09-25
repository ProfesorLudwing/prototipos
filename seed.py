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

También expone el cronograma oficial DGETI 2026-2027 y funciones
para aplicarlo a equipos desde el panel del tutor.
"""
import json
import os

import config
import db
from models import Aviso, Entregable


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
# Cronograma oficial DGETI (Concurso Nacional de Prototipos)
# Ciclo 2026-2027 · Fuente: guía cronológica y checklist de control de avance
# ============================================================
CRONOGRAMA_DGETI = [
    {
        "etapa": "inicio",
        "titulo": "1. Conformación del equipo y modalidad",
        "descripcion": (
            "Integración del equipo (1 a 4 estudiantes), definición de la "
            "modalidad (Prototipo o Emprendimiento) y registro interno en el plantel."
        ),
        "fecha_limite": "2026-10-10",
    },
    {
        "etapa": "inicio",
        "titulo": "2. Asignación de asesor",
        "descripcion": (
            "Designación del docente asesor (técnico y metodológico). "
            "Verificar constancia del curso o taller de metodología de "
            "investigación (2025 o 2026)."
        ),
        "fecha_limite": "2026-10-25",
    },
    {
        "etapa": "inicio",
        "titulo": "3. Enfoque, ética y línea PROIDET",
        "descripcion": (
            "Vinculación con un problema real / PAEC, selección de la línea "
            "PROIDET y elaboración y firma del Formato de Compromiso de "
            "Ética y Originalidad (FOCOMO)."
        ),
        "fecha_limite": "2026-10-31",
    },
    {
        "etapa": "desarrollo",
        "titulo": "4. Registro en SIGPE",
        "descripcion": (
            "Conclusión del borrador del Informe Técnico y la Bitácora de "
            "trabajo. Inserción de los datos en la plataforma oficial SIGPE."
        ),
        "fecha_limite": "2026-11-21",
    },
    {
        "etapa": "desarrollo",
        "titulo": "5. Cédulas oficiales (FOREG)",
        "descripcion": (
            "Descarga del formato impreso oficial FOREG con el folio "
            "asignado por el sistema SIGPE."
        ),
        "fecha_limite": "2026-11-24",
    },
    {
        "etapa": "desarrollo",
        "titulo": "6. Evaluación local",
        "descripcion": (
            "Realización del certamen en el plantel evaluado por 3 jurados "
            "por proyecto. Puntaje mínimo de acreditación: 80 puntos."
        ),
        "fecha_limite": "2026-12-19",
    },
    {
        "etapa": "desarrollo",
        "titulo": "7. Carga de actas",
        "descripcion": (
            "Carga en el SIGPE de los PDF firmados: Acta de Apertura, "
            "Acta de Cierre y Anexo B de Puntajes."
        ),
        "fecha_limite": "2027-01-09",
    },
    {
        "etapa": "desarrollo",
        "titulo": "8. Fase estatal",
        "descripcion": (
            "Evaluación estatal y compilación del expediente digital "
            "(FOREG, FOAPA, FOCOMO, FOAS, Informe Técnico y Carpeta Documental). "
            "Tramitar formato FOACT si hay cambios de integrantes."
        ),
        "fecha_limite": "2027-03-20",
    },
    {
        "etapa": "cierre",
        "titulo": "9. Trámites nacionales",
        "descripcion": (
            "Publicación de aceptados, actualización final en SIGPE, "
            "carga documental definitiva y atención a observaciones ANIDET."
        ),
        "fecha_limite": "2027-05-26",
    },
    {
        "etapa": "cierre",
        "titulo": "10. Evento nacional",
        "descripcion": (
            "Asistencia presencial (máximo 2 alumnos autores y 1 asesor "
            "docente), montaje de stand, exposición ante jurados nacionales "
            "y ceremonia de premiación."
        ),
        "fecha_limite": "2027-06-25",
    },
]


# ============================================================
# Utilidades de inicialización
# ============================================================
def _crear_carpeta(ruta: str) -> bool:
    if not os.path.exists(ruta):
        os.makedirs(ruta, exist_ok=True)
        return True
    return False


def _crear_json_si_falta(ruta: str, contenido_inicial) -> bool:
    if os.path.exists(ruta):
        return False
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(contenido_inicial, f, ensure_ascii=False, indent=2)
    return True


def inicializar(verbose: bool = True) -> dict:
    """Inicializa toda la estructura del proyecto. Idempotente."""
    resultado = {"carpetas_creadas": [], "archivos_creados": []}

    for ruta in [config.RUTA_DATA, config.RUTA_DOCUMENTOS, config.RUTA_ENTREGAS]:
        if _crear_carpeta(ruta):
            resultado["carpetas_creadas"].append(ruta)

    if _crear_json_si_falta(config.ARCHIVO_EQUIPOS, []):
        resultado["archivos_creados"].append(config.ARCHIVO_EQUIPOS)

    if _crear_json_si_falta(config.ARCHIVO_ENTREGABLES, []):
        resultado["archivos_creados"].append(config.ARCHIVO_ENTREGABLES)

    if _crear_json_si_falta(config.ARCHIVO_AVISOS, [AVISO_BIENVENIDA]):
        resultado["archivos_creados"].append(config.ARCHIVO_AVISOS)

    if not os.path.exists(config.ARCHIVO_BANCO):
        if verbose:
            print(f"⚠️  Falta {config.ARCHIVO_BANCO}.")
    else:
        resultado["banco_ideas"] = "OK"

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
# Cronograma DGETI — aplicación a equipos
# ============================================================
def aplicar_cronograma_a_equipo(equipo_id: str) -> int:
    """
    Crea los 10 entregables del cronograma DGETI para un equipo.
    No duplica los que ya existan (compara por título).
    Devuelve el número de entregables nuevos creados.
    """
    existentes = db.entregables_de_equipo(equipo_id)
    titulos_existentes = {e.titulo for e in existentes}

    creados = 0
    for item in CRONOGRAMA_DGETI:
        if item["titulo"] in titulos_existentes:
            continue
        nuevo = Entregable(
            id=db.nuevo_id(),
            equipo_id=equipo_id,
            etapa=item["etapa"],
            titulo=item["titulo"],
            descripcion=item["descripcion"],
            fecha_limite=item["fecha_limite"],
        )
        db.guardar_entregable(nuevo)
        creados += 1
    return creados


def aplicar_cronograma_a_todos() -> dict:
    """
    Aplica el cronograma DGETI a todos los equipos registrados.
    Devuelve un resumen: cuántos equipos y cuántos entregables nuevos.
    """
    equipos = db.get_equipos()
    total_creados = 0
    for eq in equipos:
        total_creados += aplicar_cronograma_a_equipo(eq.id)
    return {
        "equipos": len(equipos),
        "entregables_creados": total_creados,
    }


# ============================================================
# Ejecución directa
# ============================================================
if __name__ == "__main__":
    inicializar(verbose=True)