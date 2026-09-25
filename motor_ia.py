"""
motor_ia.py — Motor de propuestas de 'prototipos'.
Simula una IA usando reglas + banco de ideas (sin API, sin LLM).
Lee banco_ideas.json y combina las respuestas del alumno
para generar una propuesta lista para el equipo.

Versión 1.2 — matching con límites de palabra (evita falsos positivos).
"""
import json
import os
import re
import unicodedata
from typing import List, Dict, Optional

import config
from models import Respuesta


# ============================================================
# Utilidades de texto
# ============================================================
def _normalizar(texto: str) -> str:
    """
    Convierte a minúsculas y elimina acentos/diacríticos.
    'Contaminación del AGUA' → 'contaminacion del agua'
    """
    if not texto:
        return ""
    texto = texto.lower().strip()
    texto = "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )
    return texto


# ============================================================
# Carga del banco
# ============================================================
_CACHE_BANCO: Optional[dict] = None


def cargar_banco(forzar_recarga: bool = False) -> dict:
    """Carga banco_ideas.json. Lo cachea para no leerlo en cada llamada."""
    global _CACHE_BANCO
    if _CACHE_BANCO is None or forzar_recarga:
        ruta = config.ARCHIVO_BANCO
        if not os.path.exists(ruta):
            raise FileNotFoundError(
                f"No se encontró {ruta}. Verifica que esté en la raíz del proyecto."
            )
        with open(ruta, "r", encoding="utf-8") as f:
            _CACHE_BANCO = json.load(f)
    return _CACHE_BANCO


def listar_dominios() -> List[dict]:
    """Devuelve la lista de dominios del banco (id + nombre)."""
    banco = cargar_banco()
    return [
        {"id": d["id"], "nombre": d["nombre"]}
        for d in banco.get("dominios", [])
    ]


# ============================================================
# Valores por defecto
# ============================================================
def _linea_proidet_por_defecto() -> dict:
    return {"numero": 5, "nombre": "Desarrollo Humano, Social y Emocional"}


def _modalidades_por_defecto() -> List[str]:
    return ["prototipo", "emprendimiento"]


# ============================================================
# Detección de dominio
# ============================================================
def _texto_unido(respuestas: List[Respuesta]) -> str:
    """Une todas las respuestas en un solo texto normalizado."""
    return _normalizar(" ".join(r.respuesta for r in respuestas))


def _construir_patron(palabra_norm: str) -> str:
    """
    Construye un patrón regex que respeta límites de palabra.
    Ej: 'agua' → r'\\bagua\\b' (matchea 'el agua' pero NO 'aguantar')
    Los espacios internos de la palabra se reemplazan por \\s+ 
    para tolerar saltos de línea o dobles espacios.
    """
    # Escapamos caracteres especiales de regex
    base = re.escape(palabra_norm)
    # Permitimos varios espacios donde originalmente había uno
    base = base.replace(r"\ ", r"\s+")
    return r"\b" + base + r"\b"


def detectar_dominio(respuestas: List[Respuesta]) -> Dict:
    """
    Devuelve el dominio con más coincidencias de palabras clave.
    Usa regex con límites de palabra para evitar falsos positivos
    como 'aguantar' haciendo match con 'agua'.
    """
    texto = _texto_unido(respuestas)
    banco = cargar_banco()

    mejor = None
    mejor_puntaje = 0
    puntajes = []

    for dominio in banco.get("dominios", []):
        puntaje = 0
        for palabra in dominio.get("palabras_clave", []):
            palabra_norm = _normalizar(palabra)
            if not palabra_norm:
                continue
            patron = _construir_patron(palabra_norm)
            if re.search(patron, texto):
                puntaje += 1
        puntajes.append({
            "id": dominio["id"],
            "nombre": dominio["nombre"],
            "puntaje": puntaje,
        })
        if puntaje > mejor_puntaje:
            mejor_puntaje = puntaje
            mejor = dominio

    puntajes.sort(key=lambda p: p["puntaje"], reverse=True)

    if mejor is None:
        mejor = {
            "id": "generico",
            "nombre": "Propuesta general de impacto comunitario",
            "linea_proidet": _linea_proidet_por_defecto(),
            "modalidades_sugeridas": _modalidades_por_defecto(),
            "plantilla": _plantilla_generica(),
            "referencias_globales": [],
        }

    return {
        "dominio": mejor,
        "puntaje": mejor_puntaje,
        "alternativas": puntajes[:3],
    }


def _plantilla_generica() -> dict:
    """Plantilla de respaldo por si no se detecta ningún dominio."""
    return {
        "titulo_base": "Proyecto de innovación para {comunidad}",
        "resumen": (
            "El equipo detectó un problema en {comunidad}: {problema}. "
            "Proponemos una solución innovadora construida con recursos locales "
            "y con el objetivo de generar un impacto positivo y medible."
        ),
        "objetivo_general": (
            "Diseñar y aplicar una solución al problema detectado en {comunidad}, "
            "con impacto comunitario y posibilidad de réplica."
        ),
        "objetivos_especificos": [
            "Diagnosticar el problema con datos de la comunidad.",
            "Diseñar una solución viable con los recursos disponibles.",
            "Implementarla, medir resultados y ajustar lo necesario.",
        ],
        "aliados": [
            "Escuela y docentes",
            "Padres de familia",
            "Autoridades locales",
            "Organizaciones de la sociedad civil",
        ],
        "indicadores": [
            "Número de personas beneficiadas",
            "Cambio medible en la situación inicial",
            "Nivel de participación comunitaria",
        ],
        "riesgos": [
            "Falta de recursos",
            "Poca participación",
            "Falta de continuidad",
        ],
    }


# ============================================================
# Extracción de datos clave de las respuestas
# ============================================================
def _valor(respuestas: List[Respuesta], palabra_en_pregunta: str,
           por_defecto: str = "") -> str:
    palabra = _normalizar(palabra_en_pregunta)
    for r in respuestas:
        if palabra in _normalizar(r.pregunta):
            return r.respuesta.strip()
    return por_defecto


def _extraer_problema(respuestas: List[Respuesta]) -> str:
    p = _valor(respuestas, "problema", "")
    if not p and respuestas:
        p = respuestas[0].respuesta
    p = p.strip().rstrip(".")
    return p[:280] if len(p) > 280 else p


def _extraer_comunidad(respuestas: List[Respuesta]) -> str:
    c = _valor(respuestas, "comunidad", "")
    if not c:
        c = _valor(respuestas, "afecta", "")
    if not c:
        c = "tu comunidad"
    return c.strip().rstrip(".")[:80]


def _extraer_innovacion(respuestas: List[Respuesta]) -> str:
    return _valor(respuestas, "innovador", "")


# ============================================================
# Generación de la propuesta
# ============================================================
def generar_propuesta(respuestas: List[Respuesta],
                      nombre_equipo: str = "") -> dict:
    """
    Genera una propuesta completa a partir de las respuestas del alumno.
    Incluye línea PROIDET y modalidades sugeridas.
    """
    deteccion = detectar_dominio(respuestas)
    dominio = deteccion["dominio"]
    plantilla = dominio["plantilla"]

    problema = _extraer_problema(respuestas)
    comunidad = _extraer_comunidad(respuestas)

    reemplazos = {
        "problema":    problema or "un problema que detectamos en nuestra comunidad",
        "comunidad":   comunidad or "nuestra comunidad",
        "escuela":     config.ESCUELA,
        "equipo":      nombre_equipo or "nuestro equipo",
    }

    def _fmt(txt: str) -> str:
        try:
            return txt.format(**reemplazos)
        except (KeyError, IndexError):
            return txt

    linea_proidet = dominio.get("linea_proidet") or _linea_proidet_por_defecto()
    modalidades = dominio.get("modalidades_sugeridas") or _modalidades_por_defecto()

    propuesta = {
        "dominio_id":           dominio["id"],
        "dominio_nombre":       dominio["nombre"],
        "puntaje_coincidencia": deteccion["puntaje"],
        "linea_proidet":        linea_proidet,
        "modalidades_sugeridas": list(modalidades),
        "titulo_sugerido":      _fmt(plantilla.get("titulo_base", "")),
        "resumen":              _fmt(plantilla.get("resumen", "")),
        "objetivo_general":     _fmt(plantilla.get("objetivo_general", "")),
        "objetivos_especificos": [
            _fmt(o) for o in plantilla.get("objetivos_especificos", [])
        ],
        "aliados":              list(plantilla.get("aliados", [])),
        "indicadores":          list(plantilla.get("indicadores", [])),
        "riesgos":              list(plantilla.get("riesgos", [])),
        "referencias_globales": list(dominio.get("referencias_globales", [])),
        "alternativas":         deteccion["alternativas"],
        "innovacion_declarada": _extraer_innovacion(respuestas),
    }
    return propuesta


# ============================================================
# Sugerencia de nombre del proyecto
# ============================================================
def sugerir_nombre_proyecto(respuestas: List[Respuesta]) -> List[str]:
    """Genera 3 posibles nombres de proyecto a partir del dominio detectado."""
    deteccion = detectar_dominio(respuestas)
    dominio = deteccion["dominio"]
    comunidad = _extraer_comunidad(respuestas)
    problema = _extraer_problema(respuestas)

    palabras = [p for p in problema.split() if len(p) > 4][:3]
    nucleo = " ".join(palabras).title() if palabras else dominio["nombre"]

    sugerencias = [
        f"{dominio['nombre']} en {comunidad.title()}",
        f"{nucleo}: propuesta para {comunidad.title()}",
        f"Proyecto {dominio['nombre'].split()[0]} — {comunidad.title()}",
    ]
    vistas = set()
    unicas = []
    for s in sugerencias:
        if s not in vistas:
            vistas.add(s)
            unicas.append(s)
    return unicas