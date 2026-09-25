"""
ui_alumno.py — Vista del alumno en 'prototipos'.
Dos caminos:
  A) Alumno sin equipo → cuestionario → propuesta → registro de equipo.
  B) Alumno con equipo → dashboard: proyecto, entregables, docs y avisos.
"""
import os
from datetime import datetime

import streamlit as st

import config
import db
import motor_ia
from models import Respuesta, Equipo, Integrante, Entregable
from ui_comun import (
    header, badge_etapa, progreso_etapas, tarjeta_aviso,
    tarjeta_entregable, caja_info, mensaje_vacio,
)


# ============================================================
# Preguntas del cuestionario por bloque
# ============================================================
BLOQUES_PREGUNTAS = {
    "inicio": [
        "¿Qué problema vieron en su comunidad?",
        "¿A quiénes afecta y desde cuándo?",
        "¿Cómo se resuelve hoy ese problema?",
        "¿Por qué la solución actual no es suficiente?",
        "¿Qué pasa si nadie lo resuelve en 5 años?",
        "¿Qué proponen hacer?",
        "¿Por qué es innovador frente a lo que ya existe?",
        "¿Qué necesitan (materiales, personas, permiso, dinero)?",
        "¿Cómo sabrán si funcionó?",
    ],
    "desarrollo": [
        "¿Qué construyeron o probaron y qué falló?",
        "¿Qué cambiaron después de probar?",
        "¿Cómo involucraron a la comunidad?",
    ],
    "cierre": [
        "¿Qué lograron y cómo lo miden?",
        "¿Qué harían distinto?",
        "¿Cómo podría servir esto a otras comunidades?",
    ],
}

OPCION_OTRO_NOMBRE = "✏️ Otro (escribir mi propio nombre)"


# ============================================================
# Punto de entrada
# ============================================================
def render(usuario: dict):
    header(usuario)
    equipo = None
    if usuario.get("equipo_id"):
        equipo = db.get_equipo(usuario["equipo_id"])
    if equipo is None:
        _vista_nuevo(usuario)
    else:
        _dashboard(equipo)


# ============================================================
# A) Alumno nuevo
# ============================================================
def _vista_nuevo(usuario):
    st.subheader(f"¡Hola, {usuario['nombre']}! 👋")
    respuestas_inicio = st.session_state.get("respuestas_inicio")
    if not respuestas_inicio:
        _intro_y_cuestionario()
    else:
        _propuesta_y_registro(usuario, respuestas_inicio)


def _intro_y_cuestionario():
    caja_info(
        "Antes de registrar el equipo...",
        "Primero van a responder un cuestionario que les ayudará a definir "
        "qué proyecto quieren hacer. Al terminar, el asistente les propondrá "
        "un nombre y una estructura base.\n\n"
        "No hay respuestas correctas o incorrectas. Contesten con lo que "
        "observan en su comunidad.",
    )
    st.divider()
    st.markdown("### 📝 Cuestionario de inicio")
    st.caption("Estas 9 preguntas son la base del proyecto. Después se pueden editar.")

    with st.form("form_cuestionario_inicio"):
        respuestas = {}
        for i, pregunta in enumerate(BLOQUES_PREGUNTAS["inicio"], 1):
            respuestas[pregunta] = st.text_area(
                f"{i}. {pregunta}",
                key=f"q_inicio_{i}",
                height=80,
                max_chars=600,
                placeholder="Escriban su respuesta aquí...",
            )
        enviado = st.form_submit_button("✨ Generar propuesta", use_container_width=True)

    if enviado:
        faltantes = [p for p, r in respuestas.items() if not r.strip()]
        if len(faltantes) > 4:
            st.error(
                f"Faltan {len(faltantes)} respuestas. "
                "Llenen al menos 5 para que el asistente pueda proponer algo."
            )
        else:
            st.session_state["respuestas_inicio"] = respuestas
            st.rerun()


def _propuesta_y_registro(usuario, respuestas_dict):
    respuestas = [
        Respuesta(bloque="inicio", pregunta=p, respuesta=r)
        for p, r in respuestas_dict.items()
    ]
    propuesta = motor_ia.generar_propuesta(respuestas)
    sugerencias = motor_ia.sugerir_nombre_proyecto(respuestas)

    st.success("¡Cuestionario completado! El asistente generó una propuesta base.")

    # --- Propuesta generada ---
    with st.expander("🎯 Ver propuesta generada por el asistente", expanded=True):
        st.markdown(f"**Área detectada:** {propuesta['dominio_nombre']}")
        st.markdown(f"#### {propuesta['titulo_sugerido']}")
        st.write(propuesta["resumen"])
        st.markdown("**Objetivo general:**")
        st.write(propuesta["objetivo_general"])
        st.markdown("**Objetivos específicos:**")
        for o in propuesta["objetivos_especificos"]:
            st.markdown(f"- {o}")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Posibles aliados:**")
            for a in propuesta["aliados"]:
                st.markdown(f"- {a}")
        with col2:
            st.markdown("**Indicadores de impacto:**")
            for i in propuesta["indicadores"]:
                st.markdown(f"- {i}")

        st.markdown("**Riesgos a considerar:**")
        for r in propuesta["riesgos"]:
            st.markdown(f"- {r}")

        if propuesta["referencias_globales"]:
            st.markdown("**¿Quién más en el mundo tiene este problema?**")
            for ref in propuesta["referencias_globales"]:
                st.markdown(f"- [{ref['titulo']}]({ref['url']}) — {ref['descripcion']}")

    st.divider()
    st.markdown("### 🏷️ Registro del equipo")

    # Nombre del proyecto: elegir sugerencia o escribir propio
    opciones = sugerencias + [OPCION_OTRO_NOMBRE]
    eleccion = st.radio("Nombre del proyecto:", opciones, key="eleccion_nombre")
    if eleccion == OPCION_OTRO_NOMBRE:
        nombre_proyecto = st.text_input("Escribe el nombre del proyecto", max_chars=120)
    else:
        nombre_proyecto = eleccion

    nombre_equipo = st.text_input(
        "Nombre del equipo", max_chars=60, placeholder="Ej. Los Innovadores"
    )
    problematica = st.text_area(
        "Problemática a resolver (pueden editarla):",
        value=respuestas[0].respuesta if respuestas else "",
        max_chars=400,
        height=100,
    )

    st.markdown("**Integrantes** (tú eres el primero, mínimo 2, máximo 4):")
    integrantes = []
    for i in range(4):
        cols = st.columns([3, 2])
        with cols[0]:
            nombre = st.text_input(
                f"Integrante {i+1}",
                value=usuario["nombre"] if i == 0 else "",
                key=f"int_nombre_{i}",
                max_chars=60,
            )
        with cols[1]:
            escuela = st.text_input(
                "Escuela",
                value=config.ESCUELA,
                key=f"int_escuela_{i}",
                max_chars=60,
            )
        if nombre.strip():
            integrantes.append(Integrante(nombre=nombre.strip(), escuela=escuela.strip()))

    if st.button("✅ Registrar equipo", use_container_width=True, type="primary"):
        errores = []
        if not nombre_equipo.strip():
            errores.append("Falta el nombre del equipo.")
        if not nombre_proyecto or not nombre_proyecto.strip():
            errores.append("Falta el nombre del proyecto.")
        if len(integrantes) < 2:
            errores.append("Se necesitan al menos 2 integrantes.")
        for integ in integrantes:
            if db.alumno_ya_registrado(integ.nombre):
                errores.append(f"«{integ.nombre}» ya está registrado en otro equipo.")

        if errores:
            for e in errores:
                st.error(e)
        else:
            nuevo_eq = Equipo(
                id=db.nuevo_id(),
                nombre_equipo=nombre_equipo.strip(),
                nombre_proyecto=nombre_proyecto.strip(),
                problematica=problematica.strip(),
                etapa_actual="inicio",
                integrantes=integrantes,
                respuestas=respuestas,
                propuesta=propuesta,
            )
            db.guardar_equipo(nuevo_eq)

            # Actualizar la sesión (patrón seguro para session_state)
            usuario_actual = dict(st.session_state.get("usuario_actual", {}))
            usuario_actual["equipo_id"] = nuevo_eq.id
            st.session_state["usuario_actual"] = usuario_actual

            st.session_state.pop("respuestas_inicio", None)
            st.success("¡Equipo registrado! Redirigiendo...")
            st.rerun()


# ============================================================
# B) Alumno con equipo (dashboard)
# ============================================================
def _dashboard(equipo: Equipo):
    st.subheader(f"🚀 {equipo.nombre_proyecto}")
    st.caption(
        f"Equipo: {equipo.nombre_equipo} · "
        f"{len(equipo.integrantes)} integrantes · "
        f"{config.ESCUELA}"
    )
    badge_etapa(equipo.etapa_actual)
    st.write("")
    progreso_etapas(equipo.etapa_actual)
    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs([
        "🎯 Mi proyecto",
        "📤 Entregables",
        "📚 Documentos",
        "📢 Avisos",
    ])
    with tab1:
        _tab_proyecto(equipo)
    with tab2:
        _tab_entregables(equipo)
    with tab3:
        _tab_documentos()
    with tab4:
        _tab_avisos()


def _tab_proyecto(equipo: Equipo):
    st.markdown("#### 👥 Integrantes")
    for i in equipo.integrantes:
        st.markdown(f"- **{i.nombre}** · {i.escuela}")

    st.markdown("#### 🧩 Problemática")
    st.write(equipo.problematica or "(sin definir)")

    st.markdown("#### 🎯 Propuesta base")
    prop = equipo.propuesta or {}
    if not prop:
        st.info("Aún no hay propuesta generada.")
        return

    st.markdown(f"**Área:** {prop.get('dominio_nombre', '')}")
    st.markdown(f"**Objetivo general:** {prop.get('objetivo_general', '')}")

    with st.expander("Ver propuesta completa", expanded=False):
        for o in prop.get("objetivos_especificos", []):
            st.markdown(f"- {o}")
        st.markdown("**Aliados:**")
        for a in prop.get("aliados", []):
            st.markdown(f"- {a}")
        st.markdown("**Indicadores:**")
        for i in prop.get("indicadores", []):
            st.markdown(f"- {i}")
        if prop.get("referencias_globales"):
            st.markdown("**Referencias globales:**")
            for ref in prop["referencias_globales"]:
                st.markdown(f"- [{ref['titulo']}]({ref['url']})")

    st.divider()
    st.markdown("#### 📝 Cuestionarios por etapa")
    st.caption("El cuestionario de inicio ya quedó contestado al registrar el equipo.")

    for bloque in ["desarrollo", "cierre"]:
        preguntas = BLOQUES_PREGUNTAS[bloque]
        respondidas = [r for r in equipo.respuestas if r.bloque == bloque and r.respuesta.strip()]
        estado = "✅ Contestado" if len(respondidas) >= len(preguntas) else "⏳ Pendiente"
        with st.expander(f"{config.ETIQUETA_ETAPA[bloque]} — {estado}", expanded=False):
            _form_cuestionario_etapa(equipo, bloque, preguntas)


def _form_cuestionario_etapa(equipo: Equipo, bloque: str, preguntas: list):
    previas = {r.pregunta: r.respuesta for r in equipo.respuestas if r.bloque == bloque}
    with st.form(f"form_cuest_{bloque}"):
        nuevas = {}
        for i, p in enumerate(preguntas, 1):
            nuevas[p] = st.text_area(
                f"{i}. {p}",
                value=previas.get(p, ""),
                key=f"q_{bloque}_{i}",
                height=80,
                max_chars=600,
            )
        if st.form_submit_button("💾 Guardar respuestas", use_container_width=True):
            otras = [r for r in equipo.respuestas if r.bloque != bloque]
            equipo.respuestas = otras + [
                Respuesta(bloque=bloque, pregunta=p, respuesta=r)
                for p, r in nuevas.items() if r.strip()
            ]
            # Avanzar etapa automáticamente
            if bloque == "desarrollo" and equipo.etapa_actual == "inicio":
                equipo.etapa_actual = "desarrollo"
            if bloque == "cierre" and equipo.etapa_actual == "desarrollo":
                equipo.etapa_actual = "cierre"
            db.guardar_equipo(equipo)
            st.success("Respuestas guardadas.")
            st.rerun()


def _tab_entregables(equipo: Equipo):
    st.markdown("#### 📤 Entregables del equipo")
    st.caption(
        "🟢 a tiempo · 🟡 vence pronto · 🔴 vencido o vence hoy. "
        "Los PDFs se pueden reemplazar hasta la fecha límite."
    )

    entregables = db.entregables_de_equipo(equipo.id)
    if not entregables:
        mensaje_vacio("📭", "Aún no hay entregables asignados por el tutor.")
        return

    for ent in entregables:
        tarjeta_entregable(ent)
        with st.expander(f"📎 Subir / reemplazar PDF — {ent.titulo}", expanded=False):
            _form_subir_pdf(ent)


def _form_subir_pdf(ent: Entregable):
    if ent.archivo_pdf and os.path.exists(ent.archivo_pdf):
        st.caption(f"📄 Archivo actual: {os.path.basename(ent.archivo_pdf)}")
    archivo = st.file_uploader(
        f"Selecciona el PDF (máx. {config.MAX_PDF_MB} MB)",
        type=["pdf"],
        key=f"up_{ent.id}",
    )
    if st.button("Subir", key=f"btn_up_{ent.id}", use_container_width=True):
        if archivo is None:
            st.warning("Selecciona un archivo primero.")
        elif archivo.size > config.MAX_PDF_MB * 1024 * 1024:
            st.error(f"El archivo supera los {config.MAX_PDF_MB} MB.")
        else:
            os.makedirs(config.RUTA_ENTREGAS, exist_ok=True)
            ruta = os.path.join(config.RUTA_ENTREGAS, f"{ent.id}.pdf")
            with open(ruta, "wb") as f:
                f.write(archivo.getbuffer())
            ent.archivo_pdf = ruta
            ent.estado = "entregado"
            ent.fecha_entrega = datetime.now().isoformat(timespec="seconds")
            db.guardar_entregable(ent)
            st.success("¡PDF subido!")
            st.rerun()


def _tab_documentos():
    st.markdown("#### 📚 Documentos oficiales")
    st.caption("PDFs publicados por el tutor, disponibles para todos los equipos.")
    docs = db.listar_documentos_publicos()
    if not docs:
        mensaje_vacio("📂", "Aún no hay documentos publicados.")
        return
    for nombre in docs:
        ruta = os.path.join(config.RUTA_DOCUMENTOS, nombre)
        with open(ruta, "rb") as f:
            st.download_button(
                f"⬇️ {nombre}",
                data=f.read(),
                file_name=nombre,
                mime="application/pdf",
                key=f"doc_{nombre}",
            )


def _tab_avisos():
    st.markdown("#### 📢 Avisos del tutor")
    avisos = db.get_avisos()
    if not avisos:
        mensaje_vacio("📭", "Aún no hay avisos publicados.")
        return
    for a in avisos:
        tarjeta_aviso(a)