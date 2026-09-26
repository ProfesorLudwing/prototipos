"""
app.py — Punto de entrada de 'prototipos'.
Corre con:  streamlit run app.py
"""
import streamlit as st

import config
import auth
import seed
import ui_alumno
import ui_tutor


# ============================================================
# 1) Configuración de la página
# ============================================================
st.set_page_config(
    page_title=config.APP_NOMBRE,
    page_icon=config.ICONO,
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# 2) Preparar datos (estructura local + sincronización GitHub)
# ============================================================
def _preparar_datos():
    """
    1. Crea la estructura local si falta (data/, JSON vacíos, etc.).
    2. Si hay token de GitHub, baja los JSON más recientes.
    """
    try:
        seed.inicializar(verbose=False)
    except Exception:
        pass

    try:
        import db
        db.sincronizar_desde_github()
    except Exception:
        pass


# ============================================================
# 3) Router principal
# ============================================================
def main():
    _preparar_datos()

    usuario = auth.pantalla_login()
    if usuario is None:
        return

    rol = usuario.get("rol")

    if rol == "tutor":
        ui_tutor.render(usuario)
    elif rol == "alumno":
        ui_alumno.render(usuario)
    else:
        st.error("Rol desconocido. Cierra la sesión y vuelve a entrar.")
        if st.button("Cerrar sesión"):
            auth.cerrar_sesion()
            st.rerun()


# ============================================================
# 4) Ejecutar
# ============================================================
main()