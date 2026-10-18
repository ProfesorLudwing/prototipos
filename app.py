"""
app.py — Punto de entrada (El Director de la Orquesta) de 'prototipos'.

Este es el primer archivo que Streamlit lee y ejecuta cuando alguien entra a la app.
Su única responsabilidad es:
1. Configurar la apariencia de la página.
2. Asegurarse de que los datos estén listos (sincronizados con GitHub).
3. Mostrar el Login.
4. Redirigir al usuario a su panel correspondiente (Tutor o Alumno).
"""

import streamlit as st

# Importamos nuestros propios módulos (los archivos .py que hemos creado)
import config      # Contiene textos, colores y la contraseña del tutor.
import auth        # Maneja el inicio de sesión y el cierre de sesión.
import seed        # Prepara las carpetas y descarga los datos iniciales.
import ui_alumno   # Contiene la pantalla que ven los estudiantes.
import ui_tutor    # Contiene la pantalla de administración (la tuya).

# ============================================================
# 1) CONFIGURACIÓN DE LA PÁGINA (Debe ser lo primero que se ejecute)
# ============================================================
st.set_page_config(
    page_title=config.APP_NOMBRE,       # El texto que sale en la pestaña del navegador
    page_icon=config.ICONO,             # El emoji de la pestaña (🚀)
    layout="wide",                      # Hace que la app use todo el ancho de la pantalla
    initial_sidebar_state="collapsed",  # Oculta la barra lateral izquierda de Streamlit por defecto
)

# ============================================================
# 2) PREPARACIÓN DE DATOS
# ============================================================
def _preparar_datos():
    """
    Esta función se asegura de que la app tenga todo lo necesario para funcionar
    antes de mostrar cualquier pantalla al usuario.
    """
    # Paso 1: Revisar si existen las carpetas (data/, entregas/) y los archivos JSON.
    # Si no existen (por ejemplo, en un servidor nuevo), los crea con datos en blanco.
    try:
        seed.inicializar(verbose=False)
    except Exception:
        pass  # Si falla, no detenemos la app, solo seguimos.

    # Paso 2: Conectarse a GitHub para descargar los datos más recientes.
    # Esto es VITAL en Streamlit Cloud, porque cada vez que la app se reinicia,
    # borra los archivos locales. Al bajar los JSON de GitHub, recuperamos
    # a todos los alumnos, entregables y avisos guardados.
    try:
        import db
        db.sincronizar_desde_github()
    except Exception:
        pass

# ============================================================
# 3) EL ENRUTADOR PRINCIPAL (El corazón de app.py)
# ============================================================
def main():
    """
    Controla el flujo de la aplicación: decide qué pantalla mostrar.
    """
    # Primero, nos aseguramos de que los datos estén listos
    _preparar_datos()

    # Llamamos a la pantalla de login.
    # Si el usuario ya había iniciado sesión, esta función lo recuerda
    # (usando la memoria de Streamlit) y nos devuelve sus datos.
    usuario = auth.pantalla_login()

    # Si `usuario` es None, significa que la persona aún no se ha logueado.
    # La función `pantalla_login` ya mostró el formulario en pantalla,
    # así que usamos `return` para detener la ejecución aquí y no mostrar nada más.
    if usuario is None:
        return

    # Si llegamos aquí, el usuario ya se identificó. Revisamos qué rol tiene:
    rol = usuario.get("rol")

    if rol == "tutor":
        # Si es el tutor, cargamos todo el panel de administración
        ui_tutor.render(usuario)
        
    elif rol == "alumno":
        # Si es un alumno, cargamos su vista (cuestionario, sus entregables, etc.)
        ui_alumno.render(usuario)
        
    else:
        # Caso de error (poco probable, pero es bueno prevenirlo)
        st.error("Rol desconocido. Cierra la sesión y vuelve a entrar.")
        if st.button("Cerrar sesión"):
            auth.cerrar_sesion()
            st.rerun()

# ============================================================
# 4) PUNTO DE ARRANQUE
# ============================================================
# Esta es una convención de Python. Le dice al archivo:
# "Si soy el archivo principal que se está ejecutando, entonces corre la función main()".
if __name__ == "__main__":
    main()