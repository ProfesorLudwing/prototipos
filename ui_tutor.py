"""
ui_tutor.py — Vista del tutor (admin) en 'prototipos'.
Todo lo que solo tú puedes hacer:
  - Ver el panel general de todos los equipos
  - Editar / eliminar equipos
  - Asignar entregables con fecha límite
  - Cargar el cronograma oficial DGETI
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
import seed
from models import Aviso, Entregable, Equipo, Integrante, Asesor
from ui_comun import (
    header, badge_etapa, progreso_etapas, tarjeta_aviso,
    tarjeta_entregable, caja_info, mensaje_vacio, color_semaforo,
)
from ui_alumno import LINEAS_PROIDET


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

    total_alumnos = sum(len(e.integrantes) for e in equipos)
    total_entregables = len(entregables)
    entregados = sum(1 for e in entregables if e.estado == "entregado")
    pendientes = total_entregables - entregados

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
# 2) Equipos (ver / editar / eliminar)
# ============================================================
def _tab_equipos():
    equipos = db.get_equipos()
    if not equipos:
        mensaje_vacio("👥", "Aún no hay equipos registrados.")
        return

    st.caption(
        "Aquí puedes ver, editar o eliminar cada equipo. "
        "Usa ✏️ Editar para corregir datos mal capturados por los alumnos."
    )

    for eq in equipos:
        with st.expander(f"🚀 {eq.nombre_equipo} — {eq.nombre_proyecto}", expanded=False):
            modo_eliminar = st.session_state.get("eliminando_equipo_id") == eq.id
            modo_editar = st.session_state.get("editando_equipo_id") == eq.id

            if modo_eliminar:
                _vista_confirmar_eliminar(eq)
            elif modo_editar:
                _vista_editar_equipo(eq)
            else:
                _vista_ver_equipo(eq)


def _vista_ver_equipo(eq):
    badge_etapa(eq.etapa_actual)
    st.write("")
    progreso_etapas(eq.etapa_actual)
    st.divider()

    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown("**👥 Estudiantes**")
        if eq.integrantes:
            for i in eq.integrantes:
                st.markdown(f"- {i.nombre} · {i.escuela}")
        else:
            st.caption("(sin estudiantes)")

        st.markdown("**👨‍🏫 Asesores**")
        if eq.asesores:
            for a in eq.asesores:
                rol = {
                    "tecnico": "técnico",
                    "metodologico": "metodológico",
                    "ambos": "técnico y metodológico",
                }.get(a.rol, a.rol)
                st.markdown(f"- {a.nombre} · _{rol}_")
        else:
            st.caption("(sin asesores)")

    with c2:
        st.markdown("**📌 Datos oficiales**")
        st.markdown(f"- Modalidad: **{eq.modalidad.capitalize()}**")
        linea = eq.linea_proidet or {}
        st.markdown(
            f"- Línea PROIDET: **{linea.get('numero', '—')}. "
            f"{linea.get('nombre', '—')}**"
        )
        st.markdown(f"- Área detectada: {eq.propuesta.get('dominio_nombre', '—')}")
        st.markdown(f"- Registrado: {eq.fecha_registro.replace('T', ' ')[:16]}")
        st.markdown(f"- ID: `{eq.id}`")

    st.markdown("**🧩 Problemática**")
    st.write(eq.problematica or "(sin definir)")

    st.divider()
    c1, c2 = st.columns([2, 1])
    with c1:
        nueva = st.selectbox(
            "Cambiar etapa del proyecto:",
            options=config.ETAPAS,
            index=config.ETAPAS.index(eq.etapa_actual)
            if eq.etapa_actual in config.ETAPAS else 0,
            format_func=lambda x: config.ETIQUETA_ETAPA.get(x, x),
            key=f"etapa_{eq.id}",
        )
    with c2:
        st.write("")
        st.write("")
        if st.button("Guardar etapa", key=f"btn_etapa_{eq.id}",
                     use_container_width=True):
            eq.etapa_actual = nueva
            db.guardar_equipo(eq)
            st.rerun()

    st.divider()
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("✏️ Editar este equipo", key=f"btn_edit_{eq.id}",
                     use_container_width=True):
            st.session_state["editando_equipo_id"] = eq.id
            st.rerun()
    with c2:
        if st.button("🗑️ Eliminar equipo", key=f"btn_del_{eq.id}",
                     use_container_width=True):
            st.session_state["eliminando_equipo_id"] = eq.id
            st.rerun()


def _vista_editar_equipo(eq):
    st.warning(
        "✏️ **Modo edición**. Modifica los campos y guarda. "
        "Los cambios son permanentes."
    )

    with st.form(f"form_edit_{eq.id}"):
        col1, col2 = st.columns(2)
        with col1:
            nombre_equipo = st.text_input(
                "Nombre del equipo", value=eq.nombre_equipo, max_chars=60
            )
        with col2:
            nombre_proyecto = st.text_input(
                "Nombre del proyecto", value=eq.nombre_proyecto, max_chars=120
            )

        problematica = st.text_area(
            "Problemática", value=eq.problematica, max_chars=400, height=100
        )

        col1, col2 = st.columns(2)
        with col1:
            modalidad = st.radio(
                "Modalidad",
                options=["prototipo", "emprendimiento"],
                index=0 if eq.modalidad == "prototipo" else 1,
                format_func=lambda x: x.capitalize(),
                horizontal=True,
                key=f"edit_modalidad_{eq.id}",
            )
        with col2:
            linea_actual_num = (eq.linea_proidet or {}).get("numero", 5)
            idx_linea = next(
                (i for i, (n, _) in enumerate(LINEAS_PROIDET)
                 if n == linea_actual_num), 4
            )
            idx_linea_sel = st.selectbox(
                "Línea PROIDET",
                options=range(len(LINEAS_PROIDET)),
                index=idx_linea,
                format_func=lambda i: f"{LINEAS_PROIDET[i][0]}. {LINEAS_PROIDET[i][1]}",
                key=f"edit_linea_{eq.id}",
            )

        st.divider()
        st.markdown("**👥 Estudiantes** (1 a 4)")
        integrantes_nuevos = []
        for i in range(4):
            col1, col2 = st.columns([3, 2])
            with col1:
                nombre_actual = (
                    eq.integrantes[i].nombre if i < len(eq.integrantes) else ""
                )
                nombre = st.text_input(
                    f"Estudiante {i+1}",
                    value=nombre_actual,
                    key=f"edit_int_nombre_{i}_{eq.id}",
                    max_chars=60,
                )
            with col2:
                escuela_actual = (
                    eq.integrantes[i].escuela if i < len(eq.integrantes)
                    else config.ESCUELA
                )
                escuela = st.text_input(
                    "Escuela",
                    value=escuela_actual,
                    key=f"edit_int_escuela_{i}_{eq.id}",
                    max_chars=60,
                )
            if nombre.strip():
                integrantes_nuevos.append(
                    Integrante(nombre=nombre.strip(), escuela=escuela.strip())
                )

        st.divider()
        st.markdown("**👨‍🏫 Asesores** (1 o 2)")

        if len(eq.asesores) == 1 and eq.asesores[0].rol == "ambos":
            tipo_actual = "uno"
        else:
            tipo_actual = "dos"

        tipo_asesores = st.radio(
            "Composición de asesores:",
            options=["dos", "uno"],
            index=0 if tipo_actual == "dos" else 1,
            format_func=lambda x: (
                "Dos asesores (técnico + metodológico)"
                if x == "dos" else
                "Un solo asesor (cubre ambas funciones)"
            ),
            key=f"edit_tipo_asesores_{eq.id}",
        )

        asesores_nuevos = []
        if tipo_asesores == "dos":
            asesor_tec = next((a for a in eq.asesores if a.rol == "tecnico"), None)
            asesor_met = next((a for a in eq.asesores if a.rol == "metodologico"), None)

            col1, col2 = st.columns(2)
            with col1:
                nombre_tec = st.text_input(
                    "Asesor técnico — nombre",
                    value=asesor_tec.nombre if asesor_tec else "",
                    key=f"edit_tec_{eq.id}", max_chars=80,
                )
                cedula_tec = st.text_input(
                    "Cédula (opcional)",
                    value=asesor_tec.cedula if asesor_tec else "",
                    key=f"edit_ced_tec_{eq.id}", max_chars=30,
                )
            with col2:
                nombre_met = st.text_input(
                    "Asesor metodológico — nombre",
                    value=asesor_met.nombre if asesor_met else "",
                    key=f"edit_met_{eq.id}", max_chars=80,
                )
                cedula_met = st.text_input(
                    "Cédula (opcional)",
                    value=asesor_met.cedula if asesor_met else "",
                    key=f"edit_ced_met_{eq.id}", max_chars=30,
                )
            if nombre_tec.strip():
                asesores_nuevos.append(Asesor(
                    nombre=nombre_tec.strip(), rol="tecnico",
                    cedula=cedula_tec.strip()))
            if nombre_met.strip():
                asesores_nuevos.append(Asesor(
                    nombre=nombre_met.strip(), rol="metodologico",
                    cedula=cedula_met.strip()))
        else:
            asesor_ambos = next((a for a in eq.asesores if a.rol == "ambos"), None)
            if asesor_ambos is None and eq.asesores:
                asesor_ambos = eq.asesores[0]

            nombre_ambos = st.text_input(
                "Asesor (técnico y metodológico) — nombre",
                value=asesor_ambos.nombre if asesor_ambos else "",
                key=f"edit_ambos_{eq.id}", max_chars=80,
            )
            cedula_ambos = st.text_input(
                "Cédula (opcional)",
                value=asesor_ambos.cedula if asesor_ambos else "",
                key=f"edit_ced_ambos_{eq.id}", max_chars=30,
            )
            if nombre_ambos.strip():
                asesores_nuevos.append(Asesor(
                    nombre=nombre_ambos.strip(), rol="ambos",
                    cedula=cedula_ambos.strip()))

        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            guardar = st.form_submit_button(
                "💾 Guardar cambios", use_container_width=True, type="primary")
        with col2:
            cancelar = st.form_submit_button(
                "❌ Cancelar", use_container_width=True)

    if cancelar:
        st.session_state.pop("editando_equipo_id", None)
        st.rerun()

    if guardar:
        errores = []
        if not nombre_equipo.strip():
            errores.append("Falta el nombre del equipo.")
        if not nombre_proyecto.strip():
            errores.append("Falta el nombre del proyecto.")
        if len(integrantes_nuevos) < 1:
            errores.append("Al menos 1 estudiante.")
        if len(integrantes_nuevos) > 4:
            errores.append("Máximo 4 estudiantes.")
        if len(asesores_nuevos) < 1:
            errores.append("Al menos 1 asesor.")
        if len(asesores_nuevos) > 2:
            errores.append("Máximo 2 asesores.")

        for integ in integrantes_nuevos:
            otro = db.buscar_equipo_de_alumno(integ.nombre)
            if otro and otro.id != eq.id:
                errores.append(
                    f"«{integ.nombre}» ya está en otro equipo "
                    f"({otro.nombre_equipo})."
                )

        if errores:
            for e in errores:
                st.error(e)
        else:
            num_linea, nom_linea = LINEAS_PROIDET[idx_linea_sel]
            eq.nombre_equipo = nombre_equipo.strip()
            eq.nombre_proyecto = nombre_proyecto.strip()
            eq.problematica = problematica.strip()
            eq.modalidad = modalidad
            eq.linea_proidet = {"numero": num_linea, "nombre": nom_linea}
            eq.integrantes = integrantes_nuevos
            eq.asesores = asesores_nuevos
            db.guardar_equipo(eq)
            st.session_state.pop("editando_equipo_id", None)
            st.rerun()


def _vista_confirmar_eliminar(eq):
    n_ents = len(db.entregables_de_equipo(eq.id))
    st.error(
        f"⚠️ **¿Eliminar el equipo «{eq.nombre_equipo}»?**\n\n"
        f"Proyecto: **{eq.nombre_proyecto}**\n\n"
        f"Se eliminarán también:\n"
        f"- Los **{n_ents} entregables** del equipo\n"
        f"- Los PDFs que hayan subido\n\n"
        f"**Esta acción NO se puede deshacer.**"
    )
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button(
            "🗑️ Sí, eliminar definitivamente",
            key=f"btn_confirm_del_{eq.id}",
            use_container_width=True, type="primary",
        ):
            db.eliminar_equipo(eq.id)
            st.session_state.pop("eliminando_equipo_id", None)
            st.rerun()
    with col2:
        if st.button(
            "❌ Cancelar",
            key=f"btn_cancel_del_{eq.id}",
            use_container_width=True,
        ):
            st.session_state.pop("eliminando_equipo_id", None)
            st.rerun()


# ============================================================
# 3) Entregables
# ============================================================
def _tab_entregables():
    equipos = db.get_equipos()
    if not equipos:
        mensaje_vacio("👥", "Registra al menos un equipo primero.")
        return

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
            ruta = os.path.join(config.RUTA_DOCUMENTOS, archivo.name)
            db.guardar_pdf(ruta, archivo.getbuffer().tobytes())
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
                db.eliminar_pdf(ruta)
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