"""
ui_comun.py — Componentes visuales reutilizables de 'prototipos'.
Sin lógica de negocio. Solo pintar bonito y consistente.
Compatible con tema claro y oscuro de Streamlit.
"""
from datetime import datetime, date
from typing import Optional, List

import streamlit as st

import config
import auth


# ============================================================
# Header superior (aparece en todas las vistas)
# ============================================================
def header(usuario: dict):
    """Header con título, quién está conectado y botón de cerrar sesión."""
    col_izq, col_der = st.columns([5, 1])
    with col_izq:
        st.title(f"{config.ICONO} {config.APP_TITULO}")
        st.caption(f"{config.ESCUELA} · Registro y guía de proyectos de innovación")
    with col_der:
        st.write("")
        if usuario:
            rol = usuario.get("rol", "")
            nombre = usuario.get("nombre", "")
            etiqueta = "🧑‍🏫 Tutor" if rol == "tutor" else f"🎓 {nombre}"
            st.caption(f"Conectado: **{etiqueta}**")
            if st.button("Cerrar sesión", use_container_width=True, key="btn_cerrar_sesion"):
                auth.cerrar_sesion()
                st.rerun()
    st.divider()


# ============================================================
# Semáforo de fechas
# ============================================================
def color_semaforo(fecha_limite_iso: str, estado: str = "pendiente") -> str:
    """
    Devuelve 'verde' | 'amarillo' | 'rojo' según la fecha límite.
    Si el entregable ya está 'entregado', siempre devuelve 'verde'.
    """
    if estado == "entregado":
        return "verde"

    try:
        fecha = datetime.fromisoformat(fecha_limite_iso).date()
    except (ValueError, TypeError):
        return "verde"

    dias = (fecha - date.today()).days

    if dias < config.DIAS_ROJO:
        return "rojo"
    if dias <= config.DIAS_AMARILLO:
        return "amarillo"
    return "verde"


def etiqueta_dias(fecha_limite_iso: str, estado: str = "pendiente") -> str:
    """Texto humano: 'Vence en 3 días' / 'Vencido hace 2 días' / 'Entregado'."""
    if estado == "entregado":
        return "Entregado"

    try:
        fecha = datetime.fromisoformat(fecha_limite_iso).date()
    except (ValueError, TypeError):
        return "Sin fecha"

    dias = (fecha - date.today()).days

    if dias < 0:
        return f"Vencido hace {abs(dias)} día(s)"
    if dias == 0:
        return "Vence hoy"
    if dias == 1:
        return "Vence mañana"
    return f"Vence en {dias} días"


# ============================================================
# Tarjeta de entregable (con color de semáforo)
# ============================================================
def tarjeta_entregable(entregable, mostrar_boton: bool = False,
                       key_boton: str = ""):
    """
    Pinta un entregable como tarjeta con color de semáforo.
    Devuelve True si el usuario presionó el botón (y mostrar_boton=True).
    """
    color = color_semaforo(entregable.fecha_limite, entregable.estado)
    bg = config.COLORES_SEMAFORO[color]
    txt_blanco = "white" if color in ("rojo", "verde") else "black"

    st.markdown(
        f"""
        <div style="
            background-color:{bg};
            color:{txt_blanco};
            padding:12px 16px;
            border-radius:8px;
            margin-bottom:8px;
            line-height:1.35em;
        ">
            <b>{entregable.titulo}</b>
            <span style="float:right; font-size:0.85em; opacity:0.9;">
                {etiqueta_dias(entregable.fecha_limite, entregable.estado)}
            </span>
            <div style="font-size:0.9em; margin-top:6px; opacity:0.95;">
                {entregable.descripcion}
            </div>
            <div style="font-size:0.8em; margin-top:6px; opacity:0.85;">
                Etapa: {config.ETIQUETA_ETAPA.get(entregable.etapa, entregable.etapa)}
                · Fecha límite: {entregable.fecha_limite}
                · Estado: <b>{entregable.estado}</b>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if mostrar_boton:
        return st.button(
            "📤 Subir / reemplazar PDF",
            key=key_boton or f"btn_ent_{entregable.id}",
            use_container_width=False,
        )
    return False


# ============================================================
# Tarjeta de aviso
# ============================================================
def tarjeta_aviso(aviso):
    """Pinta un aviso como bloque informativo. Compatible con tema claro/oscuro."""
    st.markdown(
        f"""
        <div style="
            border-left:5px solid #0d6efd;
            background-color:#e7f1ff;
            color:#0a2540;
            padding:12px 16px;
            border-radius:6px;
            margin-bottom:10px;
        ">
            <div style="font-weight:600; margin-bottom:4px; color:#0a2540;">
                📢 {aviso.titulo}
            </div>
            <div style="font-size:0.9em; white-space:pre-wrap; color:#0a2540;">
                {aviso.contenido}
            </div>
            <div style="font-size:0.75em; color:#5a6b7c; margin-top:6px;">
                {aviso.fecha.replace('T', ' ')[:16]}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# Etiqueta de etapa (badge)
# ============================================================
def badge_etapa(etapa: str):
    """Pinta una etiqueta de etapa del proyecto."""
    etiqueta = config.ETIQUETA_ETAPA.get(etapa, etapa)
    colores = {
        "inicio":     "#0d6efd",
        "desarrollo": "#fd7e14",
        "cierre":     "#198754",
    }
    color = colores.get(etapa, "#6c757d")
    st.markdown(
        f"""
        <span style="
            display:inline-block;
            background-color:{color};
            color:white;
            padding:4px 10px;
            border-radius:12px;
            font-size:0.8em;
            font-weight:500;
        ">{etiqueta}</span>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# Caja informativa
# ============================================================
def caja_info(titulo: str, texto: str, color: str = "#0d6efd"):
    """Caja con borde de color a la izquierda. Texto legible en tema claro y oscuro."""
    st.markdown(
        f"""
        <div style="
            border-left:5px solid {color};
            background-color:#e7f1ff;
            color:#0a2540;
            padding:12px 16px;
            border-radius:6px;
            margin-bottom:10px;
        ">
            <div style="font-weight:600; margin-bottom:4px; color:#0a2540;">
                {titulo}
            </div>
            <div style="font-size:0.9em; white-space:pre-wrap; color:#0a2540;">
                {texto}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# Barra de progreso por etapas
# ============================================================
def progreso_etapas(etapa_actual: str):
    """Pinta las 3 etapas resaltando la actual."""
    etapas = config.ETAPAS
    if etapa_actual not in etapas:
        etapa_actual = etapas[0]
    idx = etapas.index(etapa_actual)

    cols = st.columns(len(etapas))
    for i, etapa in enumerate(etapas):
        with cols[i]:
            if i < idx:
                simbolo = "✅"
                color = "#198754"
            elif i == idx:
                simbolo = "▶️"
                color = "#0d6efd"
            else:
                simbolo = "⏳"
                color = "#6c757d"
            st.markdown(
                f"""
                <div style="text-align:center; padding:8px; border-radius:6px;
                            border:2px solid {color}; font-size:0.85em;">
                    <div style="font-size:1.2em;">{simbolo}</div>
                    <div style="font-weight:600;">{config.ETIQUETA_ETAPA[etapa]}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ============================================================
# Mensaje vacío (cuando no hay nada que mostrar)
# ============================================================
def mensaje_vacio(icono: str, texto: str):
    """Mensaje centrado para estados vacíos."""
    st.markdown(
        f"""
        <div style="text-align:center; padding:40px 20px; color:#6c757d;">
            <div style="font-size:3em;">{icono}</div>
            <div style="margin-top:10px;">{texto}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )