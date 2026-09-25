"""
ui_tutor.py — Vista del tutor (admin) en 'prototipos'.
Todo lo que solo tú puedes hacer:
  - Ver el panel general de todos los equipos
  - Asignar entregables con fecha límite
  - Subir documentos oficiales (PDFs)
  - Publicar avisos
  - Exportar reportes
"""
import os
from datetime import datetime, date, timedelta

import streamlit as st

import config
import db
import reportes
import seed           # ← AÑADIR ESTA LÍNEA
from models import Aviso, Entregable
from ui_comun import (
    header, badge_etapa, progreso_etapas, tarjeta_aviso,
    tarjeta_entregable, caja_info, mensaje_vacio, color_semaforo,
)


# ============================================================
# Punto de entrada
# ============================================================
def render(usuario: dict):
    header(usuario)
    st.subheader("🧑‍🏫 Panel del tutor")
    st.caption(f"Administración de proyectos · {config.ESCUELA}")
    st.divider()

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Resumen",
        "👥 Equipos",
        "📤 Entregables",
        "📚 Documentos",
        "📢 Avisos",
    ])
    with tab1:
        _tab_resumen()
    with tab2:
        _tab_equipos()
    with tab3:
        _tab_entregables()
    with tab4:
        _tab_documentos()
    with tab5:
        _tab_avisos()


# ============================================================
# 1) Resumen general
# ============================================================
def _tab_resumen():
    equipos = db.get_equipos()
    entregables = db.get_entregables()

    if not equipos:
        mensaje_vacio("👥", "Aún no hay equipos registrados.")
        return

    # --- Métricas rápidas ---
    total_alumnos = sum(len(e.integrantes) for e in equipos)
    total_entregables = len(entregables)
    entregados = sum(1 for e in entregables if e.estado == "entregado")
    pendientes = total_entregables - entregados

    # Contar entregables por semáforo
    verdes = amarillos = rojos = 0
    for e in entregables:
        c = color_semaforo(e.fecha_limite, e.estado)
        if c == "verde":
            verdes += 1
        elif c == "amarillo":
            amarillos += 1
        else:
            rojos += 1

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

    # --- Tabla por equipo ---
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
    _botones_exportar()


def _botones_exportar():
    equipos = db.get_equipos()
    if not equipos:
        return

    col1, col2, col3 = st.columns(3)

    with col1:
        csv_data = reportes.generar_csv_equipos(equipos)
        st.download_button(
            "📄 Descargar CSV",
            data=csv_data,
            file_name=f"equipos_{date.today().isoformat()}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col2:
        if st.button("📕 Generar PDF", use_container_width=True):
            st.session_state["pdf_listo"] = True

    with col3:
        if st.button("🖼️ Generar JPG", use_container_width=True):
            st.session_state["jpg_listo"] = True

    if st.session_state.get("pdf_listo"):
        try:
            pdf_bytes = reportes.generar_pdf_resumen(equipos)
            st.download_button(
                "⬇️ Descargar PDF",
                data=pdf_bytes,
                file_name=f"reporte_{date.today().isoformat()}.pdf",
                mime="application/pdf",
                key="dl_pdf",
            )
        except Exception as ex:
            st.error(f"Error al generar PDF: {ex}")

    if st.session_state.get("jpg_listo"):
        try:
            jpg_bytes = reportes.generar_jpg_resumen(equipos)
            st.download_button(
                "⬇️ Descargar JPG",
                data=jpg_bytes,
                file_name=f"reporte_{date.today().isoformat()}.jpg",
                mime="image/jpeg",
                key="dl_jpg",
            )
        except Exception as ex:
            st.error(f"Error al generar JPG: {ex}")


# ============================================================
# 2) Equipos
# ============================================================
def _tab_equipos():
    equipos = db.get_equipos()
    if not equipos:
        mensaje_vacio("👥", "Aún no hay equipos registrados.")
        return

    for eq in equipos:
        with st.expander(f"🚀 {eq.nombre_equipo} — {eq.nombre_proyecto}", expanded=False):
            badge_etapa(eq.etapa_actual)
            st.write("")
            progreso_etapas(eq.etapa_actual)
            st.divider()

            c1, c2 = st.columns([1, 1])
            with c1:
                st.markdown("**Integrantes**")
                for i in eq.integrantes:
                    st.markdown(f"- {i.nombre} · {i.escuela}")
            with c2:
                st.markdown("**Problemática**")
                st.write(eq.problematica or "(sin definir)")

            st.markdown(f"**Área detectada:** {eq.propuesta.get('dominio_nombre', '—')}")

            # Cambiar etapa manualmente
            nueva = st.selectbox(
                "Cambiar etapa del proyecto:",
                options=config.ETAPAS,
                index=config.ETAPAS.index(eq.etapa_actual) if eq.etapa_actual in config.ETAPAS else 0,
                format_func=lambda x: config.ETIQUETA_ETAPA.get(x, x),
                key=f"etapa_{eq.id}",
            )
            if nueva != eq.etapa_actual:
                if st.button("Guardar etapa", key=f"btn_etapa_{eq.id}"):
                    eq.etapa_actual = nueva
                    db.guardar_equipo(eq)
                    st.success("Etapa actualizada.")
                    st.rerun()


# ============================================================
# 3) Entregables
# ============================================================
def _tab_entregables():
    equipos = db.get_equipos()
    if not equipos:
        mensaje_vacio("👥", "Registra al menos un equipo primero.")
        return

    # ---------- Cargar cronograma DGETI ----------
    st.markdown("### 📥 Cronograma oficial DGETI 2026-2027")
    st.caption(
        "Crea automáticamente los 10 entregables del cronograma oficial "
        "con sus fechas. **No duplica** los que ya existan."
    )
    col1, col2 = st.columns(2)
    with col1:
        equipo_sel_cron = st.selectbox(
            "Aplicar a un equipo:",
            options=[e.id for e in equipos],
            format_func=lambda x: next(e.nombre_equipo for e in equipos if e.id == x),
            key="cron_equipo",
        )
        if st.button("📥 Cargar a este equipo", key="btn_cron_uno"):
            n = seed.aplicar_cronograma_a_equipo(equipo_sel_cron)
            if n:
                st.success(f"✅ Se crearon {n} entregables nuevos.")
            else:
                st.info("Este equipo ya tiene todos los entregables del cronograma.")
            st.rerun()
    with col2:
        st.write("")
        st.write("")
        if st.button("📥 Cargar a TODOS los equipos", key="btn_cron_todos", type="primary"):
            res = seed.aplicar_cronograma_a_todos()
            st.success(
                f"✅ Se crearon {res['entregables_creados']} entregables nuevos "
                f"en {res['equipos']} equipo(s)."
            )
            st.rerun()

    st.divider()

    # ---------- Asignar entregable individual ----------
    st.markdown("### ➕ Asignar nuevo entregable (individual)")
    with st.form("form_nuevo_entregable"):
        col1, col2 = st.columns(2)
        with col1:
            equipo_sel = st.selectbox(
                "Equipo",
                options=[e.id for e in equipos],
                format_func=lambda x: next(e.nombre_equipo for e in equipos if e.id == x),
            )
            titulo = st.text_input("Título del entregable", max_chars=120,
                                   placeholder="Ej. Reporte de avance 1")
        with col2:
            etapa = st.selectbox(
                "Etapa",
                options=config.ETAPAS,
                format_func=lambda x: config.ETIQUETA_ETAPA.get(x, x),
            )
            fecha_lim = st.date_input("Fecha límite", value=date.today() + timedelta(days=14))
        descripcion = st.text_area("Descripción (opcional)", max_chars=400, height=80)

        if st.form_submit_button("Crear entregable", use_container_width=True):
            if not titulo.strip():
                st.error("Falta el título.")
            else:
                nuevo = Entregable(
                    id=db.nuevo_id(),
                    equipo_id=equipo_sel,
                    etapa=etapa,
                    titulo=titulo.strip(),
                    descripcion=descripcion.strip(),
                    fecha_limite=fecha_lim.isoformat(),
                )
                db.guardar_entregable(nuevo)
                st.success("Entregable creado.")
                st.rerun()

    st.divider()

    # ---------- Lista por equipo ----------
    st.markdown("### 📋 Entregables por equipo")
    for eq in equipos:
        ents = db.entregables_de_equipo(eq.id)
        with st.expander(f"🚀 {eq.nombre_equipo} — {len(ents)} entregables"):
            if not ents:
                st.caption("Sin entregables asignados.")
                continue
            for ent in ents:
                tarjeta_entregable(ent)
                if ent.archivo_pdf and os.path.exists(ent.archivo_pdf):
                    with open(ent.archivo_pdf, "rb") as f:
                        st.download_button(
                            f"⬇️ Descargar PDF de {ent.titulo}",
                            data=f.read(),
                            file_name=f"{eq.nombre_equipo}_{ent.titulo}.pdf",
                            mime="application/pdf",
                            key=f"dl_{ent.id}",
                        )
                if st.button("🗑️ Eliminar", key=f"del_{ent.id}"):
                    todos = [e for e in db.get_entregables() if e.id != ent.id]
                    import json as _json
                    with open(config.ARCHIVO_ENTREGABLES, "w", encoding="utf-8") as f:
                        _json.dump([e.to_dict() for e in todos], f, ensure_ascii=False, indent=2)
                    st.rerun()

# ============================================================
# 4) Documentos
# ============================================================
def _tab_documentos():
    st.markdown("### 📚 Documentos oficiales")
    st.caption(
        "Estos PDFs los ven todos los equipos en su pestaña 'Documentos'. "
        f"Máximo {config.MAX_PDF_MB} MB por archivo."
    )

    archivo = st.file_uploader(
        "Subir PDF",
        type=["pdf"],
        key="up_doc_tutor",
    )
    if st.button("Publicar documento", use_container_width=False):
        if archivo is None:
            st.warning("Selecciona un archivo.")
        elif archivo.size > config.MAX_PDF_MB * 1024 * 1024:
            st.error(f"El archivo supera los {config.MAX_PDF_MB} MB.")
        else:
            os.makedirs(config.RUTA_DOCUMENTOS, exist_ok=True)
            ruta = os.path.join(config.RUTA_DOCUMENTOS, archivo.name)
            with open(ruta, "wb") as f:
                f.write(archivo.getbuffer())
            st.success(f"Documento publicado: {archivo.name}")
            st.rerun()

    st.divider()
    docs = db.listar_documentos_publicos()
    if not docs:
        mensaje_vacio("📂", "Aún no hay documentos publicados.")
        return
    st.markdown("**Documentos publicados:**")
    for nombre in docs:
        ruta = os.path.join(config.RUTA_DOCUMENTOS, nombre)
        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(f"📄 `{nombre}`")
        with col2:
            if st.button("🗑️", key=f"del_doc_{nombre}", help="Eliminar"):
                os.remove(ruta)
                st.rerun()


# ============================================================
# 5) Avisos
# ============================================================
def _tab_avisos():
    st.markdown("### 📢 Publicar nuevo aviso")
    with st.form("form_nuevo_aviso"):
        titulo = st.text_input("Título", max_chars=100)
        contenido = st.text_area("Mensaje", height=120, max_chars=1000)
        if st.form_submit_button("Publicar", use_container_width=True):
            if not titulo.strip() or not contenido.strip():
                st.error("Faltan título o contenido.")
            else:
                db.guardar_aviso(Aviso(
                    id=db.nuevo_id(),
                    titulo=titulo.strip(),
                    contenido=contenido.strip(),
                ))
                st.success("Aviso publicado.")
                st.rerun()

    st.divider()
    st.markdown("### 📋 Avisos publicados")
    avisos = db.get_avisos()
    if not avisos:
        mensaje_vacio("📭", "Aún no hay avisos publicados.")
        return
    for a in avisos:
        tarjeta_aviso(a)