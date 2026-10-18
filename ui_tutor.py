"""
ui_tutor.py — Vista del tutor (admin) en 'prototipos'.
"""
import os
from datetime import date, timedelta
import streamlit as st

import config, db, reportes, seed
from models import Aviso, Entregable, Integrante, Asesor
from ui_comun import header, badge_etapa, progreso_etapas, tarjeta_aviso, tarjeta_entregable, mensaje_vacio, color_semaforo
from ui_alumno import LINEAS_PROIDET

# ============================================================
# Enrutador Principal
# ============================================================
def render(usuario: dict):
    """Muestra el panel con las 5 pestañas de administración."""
    header(usuario)
    st.subheader("🧑‍🏫 Panel del tutor")
    st.caption(f"Administración de proyectos · {config.ESCUELA}")
    st.divider()
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Resumen", "👥 Equipos", "📤 Entregables", "📚 Documentos", "📢 Avisos"])
    with tab1: _tab_resumen()
    with tab2: _tab_equipos()
    with tab3: _tab_entregables()
    with tab4: _tab_documentos()
    with tab5: _tab_avisos()

# ============================================================
# Pestaña 1: Resumen
# ============================================================
def _tab_resumen():
    """Muestra estadísticas de participación y avance general."""
    equipos = db.get_equipos()
    entregables = db.get_entregables()
    if not equipos: 
        mensaje_vacio("👥", "Aún no hay equipos registrados.")
        return

    total_alumnos = sum(len(e.integrantes) for e in equipos)
    entregados = sum(1 for e in entregables if e.estado == "entregado")
    
    # Tarjetas de métricas
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Equipos", len(equipos))
    c2.metric("Alumnos", total_alumnos)
    c3.metric("Entregados", f"{entregados}/{len(entregables)}")
    c4.metric("Pendientes", len(entregables) - entregados)

    st.divider()
    st.markdown("### Exportar reportes")
    col1, col2, col3 = st.columns(3)
    with col1: 
        st.download_button("📄 CSV", data=reportes.generar_csv_equipos(equipos), file_name="equipos.csv", mime="text/csv", use_container_width=True)
    with col2:
        if st.button("📕 Generar PDF", use_container_width=True): st.session_state["pdf"] = True
    with col3:
        if st.button("🖼️ Generar JPG", use_container_width=True): st.session_state["jpg"] = True
        
    # Botones de descarga que aparecen solo si se presionó el botón de arriba
    if st.session_state.get("pdf"): 
        st.download_button("⬇️ Descargar PDF", data=reportes.generar_pdf_resumen(equipos), file_name="reporte.pdf")
    if st.session_state.get("jpg"): 
        st.download_button("⬇️ Descargar JPG", data=reportes.generar_jpg_resumen(equipos), file_name="reporte.jpg")

# ============================================================
# Pestaña 2: Equipos
# ============================================================
def _tab_equipos():
    """Lista los equipos en expansores."""
    equipos = db.get_equipos()
    if not equipos: 
        mensaje_vacio("👥", "No hay equipos."); return
    for eq in equipos:
        with st.expander(f"🚀 {eq.nombre_equipo} — {eq.nombre_proyecto}"):
            # Dependiendo del estado, mostramos el modo ver, editar o borrar
            if st.session_state.get("eliminando") == eq.id: _vista_borrar(eq)
            elif st.session_state.get("editando") == eq.id: _vista_editar(eq)
            else: _vista_ver(eq)

def _vista_ver(eq):
    """Muestra la ficha técnica del equipo."""
    badge_etapa(eq.etapa_actual); st.write(""); progreso_etapas(eq.etapa_actual); st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**👥 Estudiantes**")
        for i in eq.integrantes: st.markdown(f"- {i.nombre} · {i.escuela}")
        st.markdown("**👨‍🏫 Asesores**")
        for a in eq.asesores: st.markdown(f"- {a.nombre}")
    with c2:
        st.markdown(f"**Modalidad:** {eq.modalidad.capitalize()}")
        st.markdown(f"**Línea:** {(eq.linea_proidet or {}).get('nombre', '—')}")
    st.markdown(f"**🧩 Problemática:** {eq.problematica}")
    st.divider()
    
    # Botones de acción
    c1, c2 = st.columns(2)
    with c1:
        if st.button("✏️ Editar", key=f"e_{eq.id}", use_container_width=True): 
            st.session_state["editando"] = eq.id; st.rerun()
    with c2:
        if st.button("🗑️ Eliminar", key=f"d_{eq.id}", use_container_width=True): 
            st.session_state["eliminando"] = eq.id; st.rerun()

def _vista_editar(eq):
    """Formulario simplificado para corregir datos del equipo."""
    with st.form(f"edit_{eq.id}"):
        nom_eq = st.text_input("Nombre equipo", value=eq.nombre_equipo)
        nom_py = st.text_input("Nombre proyecto", value=eq.nombre_proyecto)
        prob = st.text_area("Problemática", value=eq.problematica)
        mod = st.radio("Modalidad", ["prototipo", "emprendimiento"], index=0 if eq.modalidad=="prototipo" else 1, horizontal=True)
        if st.form_submit_button("Guardar"):
            eq.nombre_equipo = nom_eq; eq.nombre_proyecto = nom_py; eq.problematica = prob; eq.modalidad = mod
            db.guardar_equipo(eq); st.session_state.pop("editando"); st.rerun()
    if st.button("Cancelar"): 
        st.session_state.pop("editando"); st.rerun()

def _vista_borrar(eq):
    """Confirmación de borrado para evitar accidentes."""
    st.error(f"¿Eliminar {eq.nombre_equipo}?")
    if st.button("Sí, borrar", type="primary"):
        db.eliminar_equipo(eq.id); st.session_state.pop("eliminando"); st.rerun()
    if st.button("Cancelar"): 
        st.session_state.pop("eliminando"); st.rerun()

# ============================================================
# Pestaña 3: Entregables
# ============================================================
def _tab_entregables():
    """Permite cargar el cronograma, crear entregables y ver los archivos subidos."""
    equipos = db.get_equipos()
    if not equipos: 
        mensaje_vacio("👥", "No hay equipos."); return

    st.markdown("### 📥 Cronograma oficial DGETI")
    c1, c2 = st.columns(2)
    with c1:
        eq_id = st.selectbox("Aplicar a un equipo:", options=[e.id for e in equipos], format_func=lambda x: next(e.nombre_equipo for e in equipos if e.id == x))
        if st.button("Cargar a este equipo"):
            n = seed.aplicar_cronograma_a_equipo(eq_id); st.success(f"{n} creados."); st.rerun()
    with c2:
        st.write(""); st.write("")
        if st.button("📥 Cargar a TODOS", type="primary"):
            res = seed.aplicar_cronograma_a_todos(); st.success(f"{res['entregables_creados']} creados."); st.rerun()

    st.divider()
    for eq in equipos:
        ents = db.entregables_de_equipo(eq.id)
        with st.expander(f"🚀 {eq.nombre_equipo} — {len(ents)} entregables"):
            if not ents: st.caption("Sin entregables.")
            for ent in ents:
                tarjeta_entregable(ent)
                
                # --- AQUI MOSTRAMOS TODOS LOS ARCHIVOS (PDF o WORD) QUE SUBIO EL EQUIPO ---
                if ent.archivos_pdf:
                    st.markdown("**Archivos entregados:**")
                    for archivo in ent.archivos_pdf:
                        if os.path.exists(archivo):
                            nombre_base = os.path.basename(archivo)
                            # Detecta el tipo de archivo para mostrarlo correctamente
                            mime_type = "application/pdf" if archivo.lower().endswith(".pdf") else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                            with open(archivo, "rb") as f:
                                st.download_button(f"⬇️ {nombre_base}", data=f.read(), file_name=nombre_base, mime=mime_type, key=f"dl_{archivo}")
                
                # Botón para eliminar el entregable (y sus archivos)
                if st.button("🗑️ Eliminar entregable", key=f"del_{ent.id}"):
                    db.eliminar_entregable(ent.id); st.rerun()

# ============================================================
# Pestaña 4: Documentos Públicos
# ============================================================
def _tab_documentos():
    """Muestra y permite subir los formatos oficiales."""
    st.markdown("### 📚 Documentos oficiales")
    archivo = st.file_uploader("Subir archivo", type=["pdf", "docx"], key="up_doc")
    if st.button("Publicar documento"):
        if archivo:
            ruta = os.path.join(config.RUTA_DOCUMENTOS, archivo.name)
            db.guardar_pdf(ruta, archivo.getbuffer().tobytes())
            st.success("Publicado."); st.rerun()

    st.divider()
    docs = db.listar_documentos_publicos()
    if not docs: mensaje_vacio("📂", "No hay documentos.")
    for nombre in docs:
        ruta = os.path.join(config.RUTA_DOCUMENTOS, nombre)
        c1, c2 = st.columns([5, 1])
        with c1: st.markdown(f"📄 `{nombre}`")
        with c2:
            if st.button("🗑️", key=f"del_doc_{nombre}"):
                db.eliminar_pdf(ruta); st.rerun()
                
        mime_type = "application/pdf" if nombre.lower().endswith(".pdf") else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        with open(ruta, "rb") as f:
            st.download_button(f"⬇️ Descargar {nombre}", data=f.read(), file_name=nombre, mime=mime_type, key=f"doc_{nombre}")

# ============================================================
# Pestaña 5: Avisos
# ============================================================
def _tab_avisos():
    """Muestra el formulario para crear avisos y la lista de ya creados."""
    st.markdown("### 📢 Nuevo aviso")
    with st.form("aviso"):
        titulo = st.text_input("Título")
        contenido = st.text_area("Mensaje")
        if st.form_submit_button("Publicar"):
            if titulo.strip() and contenido.strip():
                db.guardar_aviso(Aviso(id=db.nuevo_id(), titulo=titulo, contenido=contenido)); st.rerun()
    st.divider()
    for a in db.get_avisos(): tarjeta_aviso(a)