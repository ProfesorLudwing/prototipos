"""
models.py — Entidades de la app 'prototipos'.
Cada clase representa un objeto que se guarda como JSON en data/.
No contiene lógica de negocio, solo estructura de datos.
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional


def _ahora() -> str:
    """Devuelve la fecha/hora actual en formato ISO (ordenable)."""
    return datetime.now().isoformat(timespec="seconds")


# ============================================================
# Integrante — un estudiante dentro de un equipo
# ============================================================
@dataclass
class Integrante:
    nombre: str
    escuela: str = "CBTIS 303"

    @classmethod
    def from_dict(cls, d: dict) -> "Integrante":
        return cls(
            nombre=d.get("nombre", ""),
            escuela=d.get("escuela", "CBTIS 303"),
        )


# ============================================================
# Asesor — un docente que guía al equipo
# rol: "tecnico" | "metodologico" | "ambos"
# ============================================================
@dataclass
class Asesor:
    nombre: str
    rol: str = "ambos"
    cedula: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "Asesor":
        return cls(
            nombre=d.get("nombre", ""),
            rol=d.get("rol", "ambos"),
            cedula=d.get("cedula", ""),
        )


# ============================================================
# Respuesta — una respuesta del cuestionario guiado
# ============================================================
@dataclass
class Respuesta:
    bloque: str      # "inicio" | "desarrollo" | "cierre"
    pregunta: str
    respuesta: str

    @classmethod
    def from_dict(cls, d: dict) -> "Respuesta":
        return cls(
            bloque=d.get("bloque", ""),
            pregunta=d.get("pregunta", ""),
            respuesta=d.get("respuesta", ""),
        )


# ============================================================
# Equipo — un equipo con su proyecto
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
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Equipo":
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

    def nombres_integrantes(self) -> List[str]:
        return [i.nombre for i in self.integrantes]

    def nombres_asesores(self) -> List[str]:
        return [a.nombre for a in self.asesores]

    def etiqueta_asesores(self) -> str:
        """Texto resumido para mostrar en UI."""
        if not self.asesores:
            return "(sin asesores)"
        if len(self.asesores) == 1:
            a = self.asesores[0]
            if a.rol == "ambos":
                return f"{a.nombre} (técnico y metodológico)"
            return f"{a.nombre} ({a.rol})"
        return " + ".join(a.nombre for a in self.asesores)


# ============================================================
# Entregable — un PDF que el equipo debe subir
# ============================================================
@dataclass
class Entregable:
    id: str
    equipo_id: str
    etapa: str                    # "inicio" | "desarrollo" | "cierre"
    titulo: str
    descripcion: str
    fecha_limite: str             # ISO
    estado: str = "pendiente"     # "pendiente" | "entregado"
    archivo_pdf: Optional[str] = None
    fecha_entrega: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Entregable":
        return cls(
            id=d["id"],
            equipo_id=d["equipo_id"],
            etapa=d.get("etapa", "inicio"),
            titulo=d.get("titulo", ""),
            descripcion=d.get("descripcion", ""),
            fecha_limite=d.get("fecha_limite", ""),
            estado=d.get("estado", "pendiente"),
            archivo_pdf=d.get("archivo_pdf"),
            fecha_entrega=d.get("fecha_entrega"),
        )


# ============================================================
# Aviso — mensaje público que solo el tutor publica
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
        return cls(
            id=d["id"],
            titulo=d.get("titulo", ""),
            contenido=d.get("contenido", ""),
            fecha=d.get("fecha", _ahora()),
        )