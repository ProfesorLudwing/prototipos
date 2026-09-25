"""
auth.py — Identificación simple para 'prototipos'.
No hay usuarios con contraseña propios; solo:
  - Tutor (tú): entra con la contraseña definida en config.py
  - Alumno: entra escribiendo su nombre
Guarda la sesión en st.session_state para no pedirla en cada rerun.
"""
import streamlit as st

import config
import db


CLAVE_SESION = "usuario_actual"


# ============================================================
# API principal
# ============================================================
def usuario_actual():
    """Devuelve el usuario en sesión o None."""
    return st.session_state.get(CLAVE_SESION)


def cerrar_sesion():
    """Elimina la sesión actual."""
    st.session_state.pop(CLAVE_SESION, None)


def pantalla_login():
    """
    Muestra la pantalla de login.
    Devuelve el usuario dict si ya inició sesión, o None si aún no.
    """
    # Si ya hay sesión, devolverla sin volver a pedir datos
    usuario = usuario_actual()
    if usuario is not None:
        return usuario

    # --- Encabezado ---
    st.title(f"{config.ICONO} {config.APP_TITULO}")
    st.caption(f"{config.ESCUELA} · Registro y guía de proyectos de innovación")
    st.divider()

    st.subheader("¿Cómo quieres entrar?")
    tab_alumno, tab_tutor = st.tabs(["🎓 Soy alumno/a", "🧑‍🏫 Soy tutor/a"])

    # ============================================================
    # Pestaña Alumno
    # ============================================================
    with tab_alumno:
        st.caption(
            "Escribe tu nombre tal como lo vas a usar en tu equipo. "
            "Si ya estás registrado, te llevamos directo a tu proyecto."
        )
        with st.form("form_login_alumno", clear_on_submit=False):
            nombre = st.text_input(
                "Tu nombre",
                placeholder="Ej. Ana López",
                max_chars=60,
            )
            enviado = st.form_submit_button("Entrar", use_container_width=True)

        if enviado:
            nombre = nombre.strip()
            if len(nombre) < 3:
                st.error("Escribe tu nombre completo (mínimo 3 letras).")
            else:
                equipo = db.buscar_equipo_de_alumno(nombre)
                st.session_state[CLAVE_SESION] = {
                    "rol": "alumno",
                    "nombre": nombre,
                    "equipo_id": equipo.id if equipo else None,
                }
                st.rerun()

    # ============================================================
    # Pestaña Tutor
    # ============================================================
    with tab_tutor:
        st.caption(
            "Acceso reservado para el tutor del proyecto. "
            "Aquí puedes publicar avisos, subir documentos oficiales "
            "y ver el avance de todos los equipos."
        )
        with st.form("form_login_tutor", clear_on_submit=False):
            pwd = st.text_input("Contraseña", type="password")
            enviado_t = st.form_submit_button("Entrar como tutor", use_container_width=True)

        if enviado_t:
            if pwd == config.PASSWORD_TUTOR:
                st.session_state[CLAVE_SESION] = {
                    "rol": "tutor",
                    "nombre": "Tutor",
                }
                st.rerun()
            else:
                st.error("Contraseña incorrecta.")

    return usuario_actual()


# ============================================================
# Helpers de conveniencia
# ============================================================
def es_tutor() -> bool:
    u = usuario_actual()
    return bool(u and u.get("rol") == "tutor")


def es_alumno() -> bool:
    u = usuario_actual()
    return bool(u and u.get("rol") == "alumno")


def nombre_actual() -> str:
    u = usuario_actual()
    return u["nombre"] if u else ""


def equipo_id_actual():
    """Devuelve el id del equipo del alumno, o None si aún no tiene."""
    u = usuario_actual()
    if not u or u.get("rol") != "alumno":
        return None
    return u.get("equipo_id")