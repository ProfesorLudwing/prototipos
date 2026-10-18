"""
models.py — Entidades de la app 'prototipos'.
Define las clases que se convierten a JSON y se guardan en GitHub.
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional

def _ahora() -> str:
    """Devuelve la fecha y hora actual en formato ISO (ej. 2026-10-18T12:00:00)."""
    return datetime.now().isoformat(timespec="seconds")

# ============================================================
# Clase Integrante: Un alumno dentro del equipo.
# ============================================================
@dataclass
class Integrante:
    nombre: str
    escuela: str = "CBTIS 303"

    @classmethod
    def from_dict(cls, d: dict) -> "Integrante":
        """Convierte un diccionario de JSON a un objeto Integrante."""
        return cls(nombre=d.get("nombre", ""), escuela=d.get("escuela", "CBTIS 303"))

# ============================================================
# Clase Asesor: Docente que guía al equipo (técnico o metodológico).
# ============================================================
@dataclass
class Asesor:
    nombre: str
    rol: str = "ambos"  # Puede ser: "tecnico", "metodologico" o "ambos"
    cedula: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "Asesor":
        return cls(nombre=d.get("nombre", ""), rol=d.get("rol", "ambos"), cedula=d.get("cedula", ""))

# ============================================================
# Clase Respuesta: Guarda lo que el alumno contestó en el cuestionario.
# ============================================================
@dataclass
class Respuesta:
    bloque: str      # "inicio", "desarrollo" o "cierre"
    pregunta: str
    respuesta: str

    @classmethod
    def from_dict(cls, d: dict) -> "Respuesta":
        return cls(bloque=d.get("bloque", ""), pregunta=d.get("pregunta", ""), respuesta=d.get("respuesta", ""))

# ============================================================
# Clase Equipo: Contiene todos los datos de un proyecto.
# ============================================================
@dataclass
class Equipo:
    id: str
    nombre_equipo: str
    nombre_proyecto: str
    problematica: str
    etapa_actual: str = "inicio"
    integrantes: List[Integrante] = field(default_factory=list)
    asesores: List[Asesor] = field(default_factory=list)
    modalidad: str = "prototipo"
    linea_proidet: dict = field(default_factory=dict)
    respuestas: List[Respuesta] = field(default_factory=list)
    propuesta: dict = field(default_factory=dict)
    fecha_registro: str = field(default_factory=_ahora)

    def to_dict(self) -> dict:
        """Convierte el objeto a un diccionario para guardarlo en JSON."""
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Equipo":
        """Reconstruye un objeto Equipo a partir del JSON de GitHub."""
        return cls(
            id=d["id"],
            nombre_equipo=d.get("nombre_equipo", ""),
            nombre_proyecto=d.get("nombre_proyecto", ""),
            problematica=d.get("problematica", ""),
            etapa_actual=d.get("etapa_actual", "inicio"),
            integrantes=[Integrante.from_dict(i) for i in d.get("integrantes", [])],
            asesores=[Asesor.from_dict(a) for a in d.get("asesores", [])],
            modalidad=d.get("modalidad", "prototipo"),
            linea_proidet=d.get("linea_proidet", {}),
            respuestas=[Respuesta.from_dict(r) for r in d.get("respuestas", [])],
            propuesta=d.get("propuesta", {}),
            fecha_registro=d.get("fecha_registro", _ahora()),
        )

# ============================================================
# Clase Entregable: Tareas o documentos que el equipo debe subir.
# ============================================================
@dataclass
class Entregable:
    id: str
    equipo_id: str
    etapa: str
    titulo: str
    descripcion: str
    fecha_limite: str
    estado: str = "pendiente"
    # AHORA ES UNA LISTA: Permite guardar varios archivos por entregable
    archivos_pdf: List[str] = field(default_factory=list) 
    fecha_entrega: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Entregable":
        """Reconstruye el entregable. Incluye un parche para datos viejos."""
        # Parche de compatibilidad: Si el JSON viejo tiene "archivo_pdf" (singular), 
        # lo metemos en la lista "archivos_pdf" (plural) para no perder el archivo.
        archivos = d.get("archivos_pdf", [])
        if not archivos and d.get("archivo_pdf"):
            archivos = [d["archivo_pdf"]]

        return cls(
            id=d["id"],
            equipo_id=d["equipo_id"],
            etapa=d.get("etapa", "inicio"),
            titulo=d.get("titulo", ""),
            descripcion=d.get("descripcion", ""),
            fecha_limite=d.get("fecha_limite", ""),
            estado=d.get("estado", "pendiente"),
            archivos_pdf=archivos,
            fecha_entrega=d.get("fecha_entrega"),
        )

# ============================================================
# Clase Aviso: Mensajes del tutor para todos los equipos.
# ============================================================
@dataclass
class Aviso:
    id: str
    titulo: str
    contenido: str
    fecha: str = field(default_factory=_ahora)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Aviso":
        return cls(id=d["id"], titulo=d.get("titulo", ""), contenido=d.get("contenido", ""), fecha=d.get("fecha", _ahora()))