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
# 1) Configuración de la página (debe ir ANTES de cualquier st.*)
# ============================================================
st.set_page_config(
    page_title=config.APP_NOMBRE,
    page_icon=config.ICONO,
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# 2) Asegurar que la estructura de datos existe (sin verbose)
# ============================================================
def _asegurar_datos():
    try:
        seed.inicializar(verbose=False)
    except Exception:
        # No queremos que un fallo aquí impida abrir la app.
        pass


# ============================================================
# 3) Router principal (función, para poder usar return limpio)
# ============================================================
def main():
    _asegurar_datos()

    # --- Login ---
    usuario = auth.pantalla_login()
    if usuario is None:
        # Aún no se identifica. pantalla_login ya mostró el formulario.
        return

    # --- Router por rol ---
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
# 4) Ejecutar (Streamlit llama al script; nosotros disparamos main)
# ============================================================
main()