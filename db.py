"""
db.py — Capa de acceso a datos de 'prototipos'.
Guarda todo en archivos JSON dentro de data/.
En el Paso 9 se le añadirá sincronización con GitHub API.
"""
import json
import os
import uuid
from typing import List, Optional

import config
from models import Equipo, Integrante, Respuesta, Entregable, Aviso


# ============================================================
# Utilidades internas
# ============================================================
def nuevo_id() -> str:
    """Genera un id corto y único (8 caracteres)."""
    return uuid.uuid4().hex[:8]


def _asegurar_carpetas():
    """Crea las carpetas necesarias si no existen."""
    os.makedirs(config.RUTA_DATA, exist_ok=True)
    os.makedirs(config.RUTA_DOCUMENTOS, exist_ok=True)
    os.makedirs(config.RUTA_ENTREGAS, exist_ok=True)


def _cargar_json(ruta: str, por_defecto):
    """Lee un JSON. Si no existe o está corrupto, devuelve el valor por defecto."""
    _asegurar_carpetas()
    if not os.path.exists(ruta):
        return por_defecto
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return por_defecto


def _guardar_json(ruta: str, datos):
    """Escribe un JSON con formato legible (no en una sola línea)."""
    _asegurar_carpetas()
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)


# ============================================================
# Equipos
# ============================================================
def get_equipos() -> List[Equipo]:
    """Devuelve todos los equipos registrados."""
    crudos = _cargar_json(config.ARCHIVO_EQUIPOS, [])
    return [Equipo.from_dict(d) for d in crudos]


def guardar_equipo(equipo: Equipo) -> None:
    """Guarda o actualiza un equipo (por su id)."""
    equipos = get_equipos()
    for i, e in enumerate(equipos):
        if e.id == equipo.id:
            equipos[i] = equipo
            break
    else:
        equipos.append(equipo)
    _guardar_json(config.ARCHIVO_EQUIPOS, [e.to_dict() for e in equipos])


def get_equipo(equipo_id: str) -> Optional[Equipo]:
    """Busca un equipo por id."""
    for e in get_equipos():
        if e.id == equipo_id:
            return e
    return None


def buscar_equipo_de_alumno(nombre_alumno: str) -> Optional[Equipo]:
    """
    Devuelve el equipo al que pertenece un alumno (por nombre exacto).
    Regla: un alumno solo puede estar en 1 equipo.
    """
    objetivo = nombre_alumno.strip().lower()
    for e in get_equipos():
        for i in e.integrantes:
            if i.nombre.strip().lower() == objetivo:
                return e
    return None


def alumno_ya_registrado(nombre_alumno: str) -> bool:
    return buscar_equipo_de_alumno(nombre_alumno) is not None


# ============================================================
# Entregables
# ============================================================
def get_entregables() -> List[Entregable]:
    crudos = _cargar_json(config.ARCHIVO_ENTREGABLES, [])
    return [Entregable.from_dict(d) for d in crudos]


def entregables_de_equipo(equipo_id: str) -> List[Entregable]:
    return [e for e in get_entregables() if e.equipo_id == equipo_id]


def guardar_entregable(entregable: Entregable) -> None:
    entregables = get_entregables()
    for i, e in enumerate(entregables):
        if e.id == entregable.id:
            entregables[i] = entregable
            break
    else:
        entregables.append(entregable)
    _guardar_json(config.ARCHIVO_ENTREGABLES, [e.to_dict() for e in entregables])


def get_entregable(entregable_id: str) -> Optional[Entregable]:
    for e in get_entregables():
        if e.id == entregable_id:
            return e
    return None


# ============================================================
# Avisos
# ============================================================
def get_avisos() -> List[Aviso]:
    """Devuelve los avisos, los más recientes primero."""
    crudos = _cargar_json(config.ARCHIVO_AVISOS, [])
    avisos = [Aviso.from_dict(d) for d in crudos]
    return sorted(avisos, key=lambda a: a.fecha, reverse=True)


def guardar_aviso(aviso: Aviso) -> None:
    avisos = get_avisos()
    avisos.append(aviso)
    _guardar_json(config.ARCHIVO_AVISOS, [a.to_dict() for a in avisos])


# ============================================================
# Documentos públicos (los PDFs que sube el tutor)
# ============================================================
def listar_documentos_publicos() -> List[str]:
    """Devuelve los nombres de archivo dentro de data/documentos/."""
    _asegurar_carpetas()
    if not os.path.exists(config.RUTA_DOCUMENTOS):
        return []
    return sorted(
        f for f in os.listdir(config.RUTA_DOCUMENTOS)
        if f.lower().endswith(".pdf")
    )

# ============================================================
# Eliminar equipos (solo tutor)
# ============================================================
def eliminar_equipo(equipo_id: str) -> bool:
    """
    Elimina un equipo y todos sus entregables asociados.
    Devuelve True si encontró y eliminó el equipo.
    También borra los PDFs subidos por ese equipo.
    """
    equipos = get_equipos()
    equipos_filtrados = [e for e in equipos if e.id != equipo_id]
    if len(equipos_filtrados) == len(equipos):
        return False  # no se encontró

    # 1) Eliminar entregables del equipo
    entregables = get_entregables()
    eliminados = [e for e in entregables if e.equipo_id == equipo_id]
    entregables_filtrados = [e for e in entregables if e.equipo_id != equipo_id]
    _guardar_json(config.ARCHIVO_ENTREGABLES,
                  [e.to_dict() for e in entregables_filtrados])

    # 2) Borrar los PDFs en disco de esos entregables
    for ent in eliminados:
        if ent.archivo_pdf and os.path.exists(ent.archivo_pdf):
            try:
                os.remove(ent.archivo_pdf)
            except OSError:
                pass  # no pasa nada si falla

    # 3) Eliminar el equipo del archivo
    _guardar_json(config.ARCHIVO_EQUIPOS,
                  [e.to_dict() for e in equipos_filtrados])
    return True


# ============================================================
# Eliminar un integrante o asesor concreto (para edición)
# ============================================================
def actualizar_equipo(equipo_id: str, **cambios) -> bool:
    """
    Actualiza campos del equipo por nombre de campo.
    Uso:  db.actualizar_equipo(id, nombre_equipo='Nuevo', modalidad='prototipo')
    Devuelve True si encontró el equipo.
    """
    equipo = get_equipo(equipo_id)
    if equipo is None:
        return False
    for campo, valor in cambios.items():
        if hasattr(equipo, campo):
            setattr(equipo, campo, valor)
    guardar_equipo(equipo)
    return True