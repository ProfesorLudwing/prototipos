"""
seed.py — Inicializa la estructura de datos de 'prototipos'.
Contiene el cronograma oficial y las funciones para inyectarlo a los equipos.
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
# Cronograma oficial DGETI v6 (Concurso Nacional de Prototipos)
# ============================================================
CRONOGRAMA_DGETI = [
    # ==========================================
    # ETAPA 1: INICIO (Organización)
    # ==========================================
    {
        "etapa": "inicio",
        "titulo": "1. Conformación de equipos y asignación de asesores",
        "descripcion": "Integración de equipos (1 a 4 miembros) en Prototipos o Emprendimiento. Asignación de la pareja de asesores obligatoria (Técnico y Metodológico). (14 al 18 de Octubre)",
        "fecha_limite": "2026-10-18",
    },
    {
        "etapa": "inicio",
        "titulo": "2. Línea PROIDET y Formatos Iniciales",
        "descripcion": "Selección de la línea de investigación (Anexo A). Llenado de formatos base: FOAS (con cédulas), FOCOMO (Ética) y FOAPA (Academia). (19 al 21 de Octubre)",
        "fecha_limite": "2026-10-21",
    },
    
    # ==========================================
    # ETAPA 2: DESARROLLO (Muestras y Fase Estatal)
    # ==========================================
    {
        "etapa": "desarrollo",
        "titulo": "3. MUESTRA 1 (25% de Avance)",
        "descripcion": "Entrega del Protocolo Inicial de Investigación (planteamiento, hipótesis, objetivos) + formatos firmados FOAS, FOCOMO y FOAPA tramitado. (22 de Octubre)",
        "fecha_limite": "2026-10-22",
    },
    {
        "etapa": "desarrollo",
        "titulo": "4. MUESTRA 2 (50% de Avance)",
        "descripcion": "Revisión del 50% del Informe Técnico (marco teórico, metodología y diagramas) + Bitácora de investigación al día y avance en manuales. (05 de Noviembre)",
        "fecha_limite": "2026-11-05",
    },
    {
        "etapa": "desarrollo",
        "titulo": "5. MUESTRA 3 (75% de Avance)",
        "descripcion": "Demostración funcional en vivo del prototipo/MVP + Pre-diseño del cartel de exposición + Primer ensayo de defensa oral + Constancias de asesores. (18 de Noviembre)",
        "fecha_limite": "2026-11-18",
    },
    {
        "etapa": "desarrollo",
        "titulo": "6. MUESTRA 4 (100% Cierre de Expediente)",
        "descripcion": "Verificación final del expediente digital: FOREG, FOAPA, FOCOMO, FOAS, ...INFORME (PDF técnico final) y ...DOCUMENTOS (Bitácora, Manuales, Cartel). (26 de Noviembre)",
        "fecha_limite": "2026-11-26",
    },
    {
        "etapa": "desarrollo",
        "titulo": "7. Fase Estatal y Carga en SIGPE",
        "descripcion": "Emisión de Actas (Apertura, Cierre, Anexo B), presentación en Fase Estatal (mínimo 80 pts) y subida digital a SIGPE. (27 Nov al 03 Dic)",
        "fecha_limite": "2026-12-03",
    },

    # ==========================================
    # ETAPA 3: CIERRE (Fase Nacional)
    # ==========================================
    {
        "etapa": "cierre",
        "titulo": "8. Publicación de Clasificados",
        "descripcion": "Verificación de listas oficiales de proyectos acreditados a la Fase Nacional. (13 de Abril)",
        "fecha_limite": "2027-04-13",
    },
    {
        "etapa": "cierre",
        "titulo": "9. Carga Documental Definitiva y ANIDET",
        "descripcion": "Subida de documentación final corregida a SIGPE (04-11 May) y atención a observaciones del comité nacional ANIDET (21-26 May).",
        "fecha_limite": "2027-05-26",
    },
    {
        "etapa": "cierre",
        "titulo": "10. Evento Presencial Fase Nacional",
        "descripcion": "Asistencia de hasta 2 alumnos autores y 1 asesor docente autorizado para montaje de stand, evaluación nacional y premiación. (21 al 25 de Junio)",
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
        print("-" * 55)
        print("Listo. Ahora puedes correr:  streamlit run app.py")

    return resultado


# ============================================================
# Cronograma DGETI — aplicación a equipos
# ============================================================
def aplicar_cronograma_a_equipo(equipo_id: str) -> int:
    """
    Crea los entregables del cronograma DGETI para un equipo.
    Usa guardado en lote para no saturar a GitHub.
    Devuelve el número de entregables nuevos creados.
    """
    existentes = db.entregables_de_equipo(equipo_id)
    titulos_existentes = {e.titulo for e in existentes}

    nuevos = []
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
        nuevos.append(nuevo)

    if nuevos:
        # Guardamos todos de golpe (una sola subida a GitHub)
        db.guardar_entregables_lote(nuevos)
        
    return len(nuevos)


def aplicar_cronograma_a_todos() -> dict:
    """
    Aplica el cronograma DGETI a todos los equipos registrados.
    Devuelve un resumen de cuántos equipos y entregables se crearon.
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