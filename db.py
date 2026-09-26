"""
db.py — Capa de acceso a datos de 'prototipos'.
Guarda todo en archivos JSON dentro de data/.
Con GitHub configurado, sincroniza para persistir en la nube.
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
    return uuid.uuid4().hex[:8]


def _asegurar_carpetas():
    os.makedirs(config.RUTA_DATA, exist_ok=True)
    os.makedirs(config.RUTA_DOCUMENTOS, exist_ok=True)
    os.makedirs(config.RUTA_ENTREGAS, exist_ok=True)


def _cargar_json(ruta: str, por_defecto):
    _asegurar_carpetas()
    if not os.path.exists(ruta):
        return por_defecto
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return por_defecto


def _guardar_json(ruta: str, datos, subir_a_github: bool = True):
    _asegurar_carpetas()
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    if subir_a_github:
        _subir_archivo_a_github(
            ruta,
            mensaje=f"[app] Actualizar {os.path.basename(ruta)}"
        )


# ============================================================
# Integración con GitHub (persistencia en la nube)
# ============================================================
_github_repo_cache = None


def _leer_secret(clave: str, por_defecto: str = "") -> str:
    """
    Lee un secret desde st.secrets (en Streamlit Cloud) o desde
    .streamlit/secrets.toml (en local), con fallback silencioso.
    """
    # Intento 1: st.secrets
    try:
        import streamlit as st
        if hasattr(st, "secrets") and clave in st.secrets:
            return st.secrets[clave]
    except Exception:
        pass
    # Intento 2: leer el toml directamente
    try:
        import toml
        ruta = ".streamlit/secrets.toml"
        if os.path.exists(ruta):
            data = toml.load(ruta)
            if clave in data:
                return data[clave]
    except Exception:
        pass
    return por_defecto


def _github_disponible() -> bool:
    return bool(_leer_secret("GITHUB_TOKEN"))


def _obtener_repo():
    """Devuelve el objeto Repository de PyGithub (cacheado)."""
    global _github_repo_cache
    if _github_repo_cache is not None:
        return _github_repo_cache
    token = _leer_secret("GITHUB_TOKEN")
    repo_nombre = _leer_secret("GITHUB_REPO")
    if not token or not repo_nombre:
        return None
    try:
        from github import Github, Auth
        g = Github(auth=Auth.Token(token))
        _github_repo_cache = g.get_repo(repo_nombre)
        return _github_repo_cache
    except Exception as e:
        print(f"[github] No se pudo autenticar: {e}")
        return None


def sincronizar_desde_github():
    """
    Descarga los JSON desde GitHub al sistema local.
    Llamar UNA vez al inicio de la app (en app.py).
    """
    if not _github_disponible():
        return
    repo = _obtener_repo()
    if repo is None:
        return

    archivos = [
        config.ARCHIVO_EQUIPOS,
        config.ARCHIVO_ENTREGABLES,
        config.ARCHIVO_AVISOS,
    ]
    for ruta in archivos:
        try:
            contenido = repo.get_contents(ruta)
            texto = contenido.decoded_content.decode("utf-8")
            _asegurar_carpetas()
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(texto)
        except Exception:
            # El archivo aún no existe en GitHub → ignorar
            pass


def _subir_archivo_a_github(ruta_local: str, mensaje: str = "[app] Update"):
    """
    Sube un archivo local a GitHub.
    Si el archivo no existe en el repo, lo crea; si existe, lo actualiza.
    Falla silenciosamente si no hay config o red.
    """
    if not _github_disponible():
        return
    repo = _obtener_repo()
    if repo is None:
        return

    try:
        with open(ruta_local, "rb") as f:
            contenido = f.read()

        branch = _leer_secret("GITHUB_BRANCH", "main")

        try:
            existente = repo.get_contents(ruta_local, ref=branch)
            repo.update_file(
                path=ruta_local,
                message=mensaje,
                content=contenido,
                sha=existente.sha,
                branch=branch,
            )
        except Exception:
            # No existe → crear
            repo.create_file(
                path=ruta_local,
                message=mensaje,
                content=contenido,
                branch=branch,
            )
    except Exception as e:
        # Nunca tumbamos la app por un fallo de red
        print(f"[github] No se pudo subir {ruta_local}: {e}")


# ============================================================
# Equipos
# ============================================================
def get_equipos() -> List[Equipo]:
    crudos = _cargar_json(config.ARCHIVO_EQUIPOS, [])
    return [Equipo.from_dict(d) for d in crudos]


def guardar_equipo(equipo: Equipo) -> None:
    equipos = get_equipos()
    for i, e in enumerate(equipos):
        if e.id == equipo.id:
            equipos[i] = equipo
            break
    else:
        equipos.append(equipo)
    _guardar_json(config.ARCHIVO_EQUIPOS, [e.to_dict() for e in equipos])


def get_equipo(equipo_id: str) -> Optional[Equipo]:
    for e in get_equipos():
        if e.id == equipo_id:
            return e
    return None


def buscar_equipo_de_alumno(nombre_alumno: str) -> Optional[Equipo]:
    objetivo = nombre_alumno.strip().lower()
    for e in get_equipos():
        for i in e.integrantes:
            if i.nombre.strip().lower() == objetivo:
                return e
    return None


def alumno_ya_registrado(nombre_alumno: str) -> bool:
    return buscar_equipo_de_alumno(nombre_alumno) is not None


def eliminar_equipo(equipo_id: str) -> bool:
    equipos = get_equipos()
    equipos_filtrados = [e for e in equipos if e.id != equipo_id]
    if len(equipos_filtrados) == len(equipos):
        return False

    entregables = get_entregables()
    eliminados = [e for e in entregables if e.equipo_id == equipo_id]
    entregables_filtrados = [e for e in entregables if e.equipo_id != equipo_id]
    _guardar_json(config.ARCHIVO_ENTREGABLES,
                  [e.to_dict() for e in entregables_filtrados])

    for ent in eliminados:
        if ent.archivo_pdf and os.path.exists(ent.archivo_pdf):
            try:
                os.remove(ent.archivo_pdf)
            except OSError:
                pass

    _guardar_json(config.ARCHIVO_EQUIPOS,
                  [e.to_dict() for e in equipos_filtrados])
    return True


def actualizar_equipo(equipo_id: str, **cambios) -> bool:
    equipo = get_equipo(equipo_id)
    if equipo is None:
        return False
    for campo, valor in cambios.items():
        if hasattr(equipo, campo):
            setattr(equipo, campo, valor)
    guardar_equipo(equipo)
    return True


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
    _guardar_json(config.ARCHIVO_ENTREGABLES,
                  [e.to_dict() for e in entregables])


def get_entregable(entregable_id: str) -> Optional[Entregable]:
    for e in get_entregables():
        if e.id == entregable_id:
            return e
    return None


# ============================================================
# Avisos
# ============================================================
def get_avisos() -> List[Aviso]:
    crudos = _cargar_json(config.ARCHIVO_AVISOS, [])
    avisos = [Aviso.from_dict(d) for d in crudos]
    return sorted(avisos, key=lambda a: a.fecha, reverse=True)


def guardar_aviso(aviso: Aviso) -> None:
    avisos = get_avisos()
    avisos.append(aviso)
    _guardar_json(config.ARCHIVO_AVISOS, [a.to_dict() for a in avisos])


# ============================================================
# Documentos públicos
# ============================================================
def listar_documentos_publicos() -> List[str]:
    _asegurar_carpetas()
    if not os.path.exists(config.RUTA_DOCUMENTOS):
        return []
    return sorted(
        f for f in os.listdir(config.RUTA_DOCUMENTOS)
        if f.lower().endswith(".pdf")
    )


# ============================================================
# Subida de archivos (con sync a GitHub)
# ============================================================
def guardar_pdf(ruta_destino: str, contenido_bytes: bytes) -> None:
    """Guarda un PDF localmente y lo sube a GitHub."""
    _asegurar_carpetas()
    os.makedirs(os.path.dirname(ruta_destino), exist_ok=True)
    with open(ruta_destino, "wb") as f:
        f.write(contenido_bytes)
    _subir_archivo_a_github(
        ruta_destino,
        mensaje=f"[app] Subir {os.path.basename(ruta_destino)}"
    )


def eliminar_pdf(ruta_local: str) -> None:
    """Elimina un PDF localmente y de GitHub."""
    # 1) Local
    if os.path.exists(ruta_local):
        try:
            os.remove(ruta_local)
        except OSError:
            pass
    # 2) GitHub
    if not _github_disponible():
        return
    repo = _obtener_repo()
    if repo is None:
        return
    try:
        branch = _leer_secret("GITHUB_BRANCH", "main")
        existente = repo.get_contents(ruta_local, ref=branch)
        repo.delete_file(
            path=ruta_local,
            message=f"[app] Eliminar {os.path.basename(ruta_local)}",
            sha=existente.sha,
            branch=branch,
        )
    except Exception as e:
        print(f"[github] No se pudo eliminar {ruta_local}: {e}")