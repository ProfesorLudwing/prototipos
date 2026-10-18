"""
ui_tutor.py — Vista del tutor (admin) en 'prototipos'.
Contiene las herramientas para gestionar equipos, entregables, documentos y avisos.
"""
import os
from datetime import date, timedelta

import streamlit as st

import config
import db
import reportes
import seed
from models import Aviso, Entregable, Integrante, Asesor
from ui_comun import (
    header, badge_etapa, progreso_etapas, tarjeta_aviso,
    tarjeta_entregable, mensaje_vacio, color_semaforo,
)
from ui_alumno import LINEAS_PROIDET


# ============================================================
# Punto de entrada principal
# ============================================================
def render(usuario: dict):
    """Muestra el panel completo del tutor con sus 5 pestañas."""
    header(usuario)
    st.subheader("🧑‍🏫 Panel del tutor")
    st.caption(f"Administración de proyectos · {config.ESCUELA}")
    st.divider()

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Resumen", "👥 Equipos", "📤 Entregables", "📚 Documentos", "📢 Avisos",
    ])
    with tab1: _tab_resumen()
    with tab2: _tab_equipos()
    with tab3: _tab_entregables()
    with tab4: _tab_documentos()
    with tab5: _tab_avisos()


# ============================================================
# 1) Pestaña: Resumen y Reportes
# ============================================================
def _tab_resumen():
    """Muestra estadísticas generales y botones para exportar reportes."""
    equipos = db.get_equipos()
    entregables = db.get_entregables()

    if not equipos:
        mensaje_vacio("👥", "Aún no hay equipos registrados.")
        return

    total_alumnos = sum(len(e.integrantes) for e in equipos)
    total_entregables = len(entregables)
    entregados = sum(1 for e in entregables if e.estado == "entregado")
    pendientes = total_entregables - entregados

    verdes = amarillos = rojos = 0
    for e in entregables:
        c = color_semaforo(e.fecha_limite, e.estado)
        if c == "verde": verdes += 1
        elif c == "amarillo": amarillos += 1
        else: rojos += 1

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Equipos", len(equipos))
    c2.metric("Alumnos", total_alumnos)
    c3.metric("Entregables entregados", f"{entregados}/{total_entregables}")
    c4.metric("Pendientes", pendientes)

    c1, c2, c3 = st.columns(3)
    c1.metric("🟢 A tiempo", verdes)
    c2.metric("🟡 Vencen pronto", amarillos)
    c3.metric("🔴 Vencidos / hoy", rojos)

    st.divider()
    st.markdown("### Estado por equipo")
    
    filas = []
    for eq in equipos:
        ents = [e for e in entregables if e.equipo_id == eq.id]
        ent_ok = sum(1 for e in ents if e.estado == "entregado")
        filas.append({
            "Equipo": eq.nombre_equipo,
            "Proyecto": eq.nombre_proyecto,
            "Etapa": config.ETIQUETA_ETAPA.get(eq.etapa_actual, eq.etapa_actual),
            "Integrantes": len(eq.integrantes),
            "Entregables": f"{ent_ok}/{len(ents)}",
        })
    st.dataframe(filas, use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("### Exportar reportes")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        csv_data = reportes.generar_csv_equipos(equipos)
        st.download_button("📄 Descargar CSV", data=csv_data, file_name=f"equipos_{date.today()}.csv", mime="text/csv", use_container_width=True)
    with col2:
        if st.button("📕 Generar PDF", use_container_width=True): st.session_state["pdf_listo"] = True
    with col3:
        if st.button("🖼️ Generar JPG", use_container_width=True): st.session_state["jpg_listo"] = True

    if st.session_state.get("pdf_listo"):
        pdf_bytes = reportes.generar_pdf_resumen(equipos)
        st.download_button("⬇️ Descargar PDF", data=pdf_bytes, file_name=f"reporte_{date.today()}.pdf", mime="application/pdf", key="dl_pdf")

    if st.session_state.get("jpg_listo"):
        jpg_bytes = reportes.generar_jpg_resumen(equipos)
        st.download_button("⬇️ Descargar JPG", data=jpg_bytes, file_name=f"reporte_{date.today()}.jpg", mime="image/jpeg", key="dl_jpg")


# ============================================================
# 2) Pestaña: Equipos (Ver, Editar, Eliminar)
# ============================================================
def _tab_equipos():
    """Muestra la lista de equipos y permite editarlos o eliminarlos."""
    equipos = db.get_equipos()
    if not equipos:
        mensaje_vacio("👥", "Aún no hay equipos registrados.")
        return

    st.caption("Usa ✏️ Editar para corregir datos o 🗑️ para borrar un equipo.")
    for eq in equipos:
        with st.expander(f"🚀 {eq.nombre_equipo} — {eq.nombre_proyecto}", expanded=False):
            # Revisamos el estado de la sesión para saber qué vista mostrar
            if st.session_state.get("eliminando_equipo_id") == eq.id:
                _vista_confirmar_eliminar(eq)
            elif st.session_state.get("editando_equipo_id") == eq.id:
                _vista_editar_equipo(eq)
            else:
                _vista_ver_equipo(eq)


def _vista_ver_equipo(eq):
    """Muestra la información a detalle de un equipo y los botones de acción."""
    badge_etapa(eq.etapa_actual)
    st.write("")
    progreso_etapas(eq.etapa_actual)
    st.divider()

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**👥 Estudiantes**")
        for i in eq.integrantes: st.markdown(f"- {i.nombre} · {i.escuela}")
        st.markdown("**👨‍🏫 Asesores**")
        for a in eq.asesores:
            rol = {"tecnico": "Técnico", "metodologico": "Metodológico", "ambos": "Ambos"}.get(a.rol, a.rol)
            st.markdown(f"- {a.nombre} · _{rol}_")
    with c2:
        st.markdown("**📌 Datos oficiales**")
        st.markdown(f"- Modalidad: **{eq.modalidad.capitalize()}**")
        linea = eq.linea_proidet or {}
        st.markdown(f"- Línea: **{linea.get('numero', '—')}. {linea.get('nombre', '—')}**")
        st.markdown(f"- Registrado: {eq.fecha_registro.replace('T', ' ')[:16]}")

    st.markdown("**🧩 Problemática**")
    st.write(eq.problematica or "(sin definir)")

    st.divider()
    
    # Selector de etapa
    c1, c2 = st.columns([2, 1])
    with c1:
        nueva = st.selectbox("Cambiar etapa:", options=config.ETAPAS, index=config.ETAPAS.index(eq.etapa_actual) if eq.etapa_actual in config.ETAPAS else 0, format_func=lambda x: config.ETIQUETA_ETAPA.get(x, x), key=f"etapa_{eq.id}")
    with c2:
        st.write(""); st.write("")
        if st.button("Guardar etapa", key=f"btn_etapa_{eq.id}", use_container_width=True):
            eq.etapa_actual = nueva
            db.guardar_equipo(eq)
            st.rerun()

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("✏️ Editar este equipo", key=f"btn_edit_{eq.id}", use_container_width=True):
            st.session_state["editando_equipo_id"] = eq.id
            st.rerun()
    with c2:
        if st.button("🗑️ Eliminar equipo", key=f"btn_del_{eq.id}", use_container_width=True):
            st.session_state["eliminando_equipo_id"] = eq.id
            st.rerun()


def _vista_editar_equipo(eq):
    """Formulario completo para modificar los datos de un equipo."""
    st.warning("✏️ Modo edición. Modifica los campos y guarda.")
    
    with st.form(f"form_edit_{eq.id}"):
        col1, col2 = st.columns(2)
        with col1: nombre_equipo = st.text_input("Nombre del equipo", value=eq.nombre_equipo)
        with col2: nombre_proyecto = st.text_input("Nombre del proyecto", value=eq.nombre_proyecto)

        problematica = st.text_area("Problemática", value=eq.problematica, height=100)
        
        col1, col2 = st.columns(2)
        with col1: modalidad = st.radio("Modalidad", ["prototipo", "emprendimiento"], index=0 if eq.modalidad == "prototipo" else 1, horizontal=True, key=f"edit_mod_{eq.id}")
        with col2:
            idx_linea = next((i for i, (n, _) in enumerate(LINEAS_PROIDET) if n == (eq.linea_proidet or {}).get("numero", 5)), 4)
            idx_linea_sel = st.selectbox("Línea PROIDET", options=range(len(LINEAS_PROIDET)), index=idx_linea, format_func=lambda i: f"{LINEAS_PROIDET[i][0]}. {LINEAS_PROIDET[i][1]}", key=f"edit_lin_{eq.id}")

        st.divider()
        st.markdown("**👥 Estudiantes** (1 a 4)")
        integrantes_nuevos = []
        for i in range(4):
            col1, col2 = st.columns([3, 2])
            with col1: nombre = st.text_input(f"Estudiante {i+1}", value=eq.integrantes[i].nombre if i < len(eq.integrantes) else "", key=f"edit_int_nom_{i}_{eq.id}")
            with col2: escuela = st.text_input("Escuela", value=eq.integrantes[i].escuela if i < len(eq.integrantes) else config.ESCUELA, key=f"edit_int_esc_{i}_{eq.id}")
            if nombre.strip(): integrantes_nuevos.append(Integrante(nombre=nombre.strip(), escuela=escuela.strip()))

        st.divider()
        st.markdown("**👨‍🏫 Asesores** (1 o 2)")
        tipo_actual = "uno" if len(eq.asesores) == 1 and eq.asesores[0].rol == "ambos" else "dos"
        tipo_asesores = st.radio("Composición:", ["dos", "uno"], index=0 if tipo_actual == "dos" else 1, format_func=lambda x: "Dos asesores" if x == "dos" else "Un solo asesor", key=f"edit_tipo_{eq.id}")

        asesores_nuevos = []
        if tipo_asesores == "dos":
            a_tec = next((a for a in eq.asesores if a.rol == "tecnico"), None)
            a_met = next((a for a in eq.asesores if a.rol == "metodologico"), None)
            col1, col2 = st.columns(2)
            with col1: nom_tec = st.text_input("Asesor técnico", value=a_tec.nombre if a_tec else "", key=f"edit_tec_{eq.id}")
            with col2: nom_met = st.text_input("Asesor metodológico", value=a_met.nombre if a_met else "", key=f"edit_met_{eq.id}")
            if nom_tec.strip(): asesores_nuevos.append(Asesor(nombre=nom_tec.strip(), rol="tecnico"))
            if nom_met.strip(): asesores_nuevos.append(Asesor(nombre=nom_met.strip(), rol="metodologico"))
        else:
            a_ambos = eq.asesores[0] if eq.asesores else None
            nom_ambos = st.text_input("Asesor (ambas funciones)", value=a_ambos.nombre if a_ambos else "", key=f"edit_amb_{eq.id}")
            if nom_ambos.strip(): asesores_nuevos.append(Asesor(nombre=nom_ambos.strip(), rol="ambos"))

        st.divider()
        col1, col2 = st.columns(2)
        with col1: guardar = st.form_submit_button("💾 Guardar cambios", type="primary", use_container_width=True)
        with col2: cancelar = st.form_submit_button("❌ Cancelar", use_container_width=True)

    if cancelar:
        st.session_state.pop("editando_equipo_id", None)
        st.rerun()

    if guardar:
        if not nombre_equipo.strip() or not nombre_proyecto.strip():
            st.error("Falta nombre de equipo o proyecto.")
        elif len(integrantes_nuevos) < 1 or len(integrantes_nuevos) > 4:
            st.error("Debe haber entre 1 y 4 estudiantes.")
        elif len(asesores_nuevos) < 1 or len(asesores_nuevos) > 2:
            st.error("Debe haber entre 1 y 2 asesores.")
        else:
            num_l, nom_l = LINEAS_PROIDET[idx_linea_sel]
            eq.nombre_equipo = nombre_equipo.strip()
            eq.nombre_proyecto = nombre_proyecto.strip()
            eq.problematica = problematica.strip()
            eq.modalidad = modalidad
            eq.linea_proidet = {"numero": num_l, "nombre": nom_l}
            eq.integrantes = integrantes_nuevos
            eq.asesores = asesores_nuevos
            db.guardar_equipo(eq)
            st.session_state.pop("editando_equipo_id", None)
            st.rerun()


def _vista_confirmar_eliminar(eq):
    """Muestra una advertencia antes de borrar un equipo permanentemente."""
    n_ents = len(db.entregables_de_equipo(eq.id))
    st.error(f"⚠️ ¿Eliminar el equipo «{eq.nombre_equipo}»?\n\nSe borrarán también sus {n_ents} entregables. Esta acción no se puede deshacer.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Sí, eliminar", key=f"conf_del_{eq.id}", type="primary"):
            db.eliminar_equipo(eq.id)
            st.session_state.pop("eliminando_equipo_id", None)
            st.rerun()
    with col2:
        if st.button("❌ Cancelar", key=f"canc_del_{eq.id}"):
            st.session_state.pop("eliminando_equipo_id", None)
            st.rerun()


# ============================================================
# 3) Pestaña: Entregables
# ============================================================
def _tab_entregables():
    """Permite cargar el cronograma oficial, crear entregables manuales y borrarlos."""
    equipos = db.get_equipos()
    if not equipos:
        mensaje_vacio("👥", "Registra al menos un equipo primero.")
        return

    st.markdown("### 📥 Cronograma oficial DGETI")
    col1, col2 = st.columns(2)
    with col1:
        eq_id = st.selectbox("Aplicar a un equipo:", options=[e.id for e in equipos], format_func=lambda x: next(e.nombre_equipo for e in equipos if e.id == x), key="cron_eq")
        if st.button("📥 Cargar a este equipo"):
            n = seed.aplicar_cronograma_a_equipo(eq_id)
            st.success(f"{n} entregables creados." if n else "Ya tiene todo.")
            st.rerun()
    with col2:
        st.write(""); st.write("")
        if st.button("📥 Cargar a TODOS", type="primary"):
            res = seed.aplicar_cronograma_a_todos()
            st.success(f"{res['entregables_creados']} entregables creados en {res['equipos']} equipos.")
            st.rerun()

    st.divider()
    st.markdown("### ➕ Asignar entregable individual")
    with st.form("form_nuevo_entregable"):
        col1, col2 = st.columns(2)
        with col1:
            eq_sel = st.selectbox("Equipo", options=[e.id for e in equipos], format_func=lambda x: next(e.nombre_equipo for e in equipos if e.id == x))
            titulo = st.text_input("Título")
        with col2:
            etapa = st.selectbox("Etapa", options=config.ETAPAS, format_func=lambda x: config.ETIQUETA_ETAPA.get(x, x))
            fecha_lim = st.date_input("Fecha límite", value=date.today() + timedelta(days=14))
        desc = st.text_area("Descripción (opcional)")
        
        if st.form_submit_button("Crear entregable"):
            if titulo.strip():
                nuevo = Entregable(id=db.nuevo_id(), equipo_id=eq_sel, etapa=etapa, titulo=titulo.strip(), descripcion=desc.strip(), fecha_limite=fecha_lim.isoformat())
                db.guardar_entregable(nuevo)
                st.success("Entregable creado.")
                st.rerun()

    st.divider()
    st.markdown("### 📋 Entregables por equipo")
    for eq in equipos:
        ents = db.entregables_de_equipo(eq.id)
        with st.expander(f"🚀 {eq.nombre_equipo} — {len(ents)} entregables"):
            if not ents: st.caption("Sin entregables asignados.")
            for ent in ents:
                tarjeta_entregable(ent)
                # Botón para descargar PDF (si existe)
                if ent.archivo_pdf and os.path.exists(ent.archivo_pdf):
                    with open(ent.archivo_pdf, "rb") as f:
                        st.download_button(f"⬇️ PDF de {ent.titulo}", data=f.read(), file_name=f"{eq.nombre_equipo}_{ent.titulo}.pdf", key=f"dl_{ent.id}")
                
                # BOTÓN DE ELIMINAR CORREGIDO (Ahora usa db.eliminar_entregable)
                if st.button("🗑️ Eliminar", key=f"del_{ent.id}"):
                    db.eliminar_entregable(ent.id)
                    st.rerun()


# ============================================================
# 4) Pestaña: Documentos Públicos
# ============================================================
def _tab_documentos():
    """Permite subir y eliminar los PDFs que ven todos los alumnos."""
    st.markdown("### 📚 Documentos oficiales")
    archivo = st.file_uploader("Subir PDF (máx. 20 MB)", type=["pdf"], key="up_doc_tutor")
    
    if st.button("Publicar documento"):
        if archivo is None: st.warning("Selecciona un archivo.")
        elif archivo.size > 20 * 1024 * 1024: st.error("Supera los 20 MB.")
        else:
            ruta = os.path.join(config.RUTA_DOCUMENTOS, archivo.name)
            db.guardar_pdf(ruta, archivo.getbuffer().tobytes())
            st.success(f"Publicado: {archivo.name}")
            st.rerun()

    st.divider()
    docs = db.listar_documentos_publicos()
    if not docs: mensaje_vacio("📂", "No hay documentos.")
    
    for nombre in docs:
        ruta = os.path.join(config.RUTA_DOCUMENTOS, nombre)
        col1, col2 = st.columns([5, 1])
        with col1: st.markdown(f"📄 `{nombre}`")
        with col2:
            if st.button("🗑️", key=f"del_doc_{nombre}", help="Eliminar"):
                db.eliminar_pdf(ruta)
                st.rerun()


# ============================================================
# 5) Pestaña: Avisos
# ============================================================
def _tab_avisos():
    """Permite crear y ver los avisos para los alumnos."""
    st.markdown("### 📢 Publicar nuevo aviso")
    with st.form("form_nuevo_aviso"):
        titulo = st.text_input("Título")
        contenido = st.text_area("Mensaje", height=120)
        if st.form_submit_button("Publicar"):
            if titulo.strip() and contenido.strip():
                db.guardar_aviso(Aviso(id=db.nuevo_id(), titulo=titulo.strip(), contenido=contenido.strip()))
                st.success("Aviso publicado.")
                st.rerun()
            else:
                st.error("Faltan datos.")

    st.divider()
    st.markdown("### 📋 Avisos publicados")
    avisos = db.get_avisos()
    if not avisos: mensaje_vacio("📭", "No hay avisos.")
    for a in avisos: tarjeta_aviso(a)