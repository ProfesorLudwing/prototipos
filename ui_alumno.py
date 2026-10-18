"""
ui_alumno.py — Vista del alumno en 'prototipos'.
Contiene el cuestionario, el registro, el dashboard y la descarga de archivos.
"""
import os
from datetime import datetime

import streamlit as st

import config
import db
import motor_ia
from models import Respuesta, Equipo, Integrante, Asesor, Entregable
from ui_comun import (
    header, badge_etapa, progreso_etapas, tarjeta_aviso,
    tarjeta_entregable, caja_info, mensaje_vacio,
)

# ============================================================
# Constantes
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

LINEAS_PROIDET = [
    (1, "Desarrollo Tecnológico"),
    (2, "Investigación Educativa"),
    (3, "Desarrollo Sustentable y Medio Ambiente"),
    (4, "Investigación en Ciencias de la Salud"),
    (5, "Desarrollo Humano, Social y Emocional"),
]

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
# A) Alumno nuevo (Cuestionario y Registro)
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
    
    with st.form("form_cuestionario_inicio"):
        respuestas = {}
        for i, pregunta in enumerate(BLOQUES_PREGUNTAS["inicio"], 1):
            respuestas[pregunta] = st.text_area(f"{i}. {pregunta}", key=f"q_inicio_{i}", height=80, max_chars=600)
        enviado = st.form_submit_button("✨ Generar propuesta", use_container_width=True)

    if enviado:
        faltantes = [p for p, r in respuestas.items() if not r.strip()]
        if len(faltantes) > 4:
            st.error(f"Faltan {len(faltantes)} respuestas. Llenen al menos 5.")
        else:
            st.session_state["respuestas_inicio"] = respuestas
            st.rerun()

def _propuesta_y_registro(usuario, respuestas_dict):
    respuestas = [Respuesta(bloque="inicio", pregunta=p, respuesta=r) for p, r in respuestas_dict.items()]
    propuesta = motor_ia.generar_propuesta(respuestas)
    sugerencias = motor_ia.sugerir_nombre_proyecto(respuestas)

    st.success("¡Cuestionario completado! El asistente generó una propuesta base.")
    with st.expander("🎯 Ver propuesta generada por el asistente", expanded=True):
        st.markdown(f"**Área detectada:** {propuesta['dominio_nombre']}")
        st.markdown(f"#### {propuesta['titulo_sugerido']}")
        st.write(propuesta["resumen"])

    st.divider()
    st.markdown("### 🏷️ Registro del equipo")

    opciones = sugerencias + [OPCION_OTRO_NOMBRE]
    eleccion = st.radio("Nombre del proyecto:", opciones, key="eleccion_nombre")
    if eleccion == OPCION_OTRO_NOMBRE:
        nombre_proyecto = st.text_input("Escribe el nombre del proyecto", max_chars=120)
    else:
        nombre_proyecto = eleccion

    nombre_equipo = st.text_input("Nombre del equipo", max_chars=60)
    modalidad = st.radio("Modalidad:", ["prototipo", "emprendimiento"], horizontal=True)
    
    idx_linea = st.selectbox("Línea PROIDET:", options=range(len(LINEAS_PROIDET)), format_func=lambda i: f"{LINEAS_PROIDET[i][0]}. {LINEAS_PROIDET[i][1]}")
    num_l, nom_l = LINEAS_PROIDET[idx_linea]

    problematica = st.text_area("Problemática:", value=respuestas[0].respuesta if respuestas else "", height=100)

    st.markdown("**Integrantes:**")
    integrantes = []
    for i in range(4):
        col1, col2 = st.columns([3, 2])
        with col1: nom = st.text_input(f"Integrante {i+1}", value=usuario["nombre"] if i == 0 else "", key=f"int_{i}")
        with col2: esc = st.text_input("Escuela", value=config.ESCUELA, key=f"esc_{i}")
        if nom.strip(): integrantes.append(Integrante(nombre=nom.strip(), escuela=esc.strip()))

    st.markdown("**Asesores:**")
    tipo_asesores = st.radio("Composición:", ["dos", "uno"], format_func=lambda x: "Dos asesores" if x=="dos" else "Un solo asesor")
    asesores = []
    if tipo_asesores == "dos":
        c1, c2 = st.columns(2)
        with c1: nom_tec = st.text_input("Asesor técnico")
        with c2: nom_met = st.text_input("Asesor metodológico")
        if nom_tec.strip(): asesores.append(Asesor(nombre=nom_tec.strip(), rol="tecnico"))
        if nom_met.strip(): asesores.append(Asesor(nombre=nom_met.strip(), rol="metodologico"))
    else:
        nom_ambos = st.text_input("Asesor (ambas funciones)")
        if nom_ambos.strip(): asesores.append(Asesor(nombre=nom_ambos.strip(), rol="ambos"))

    if st.button("✅ Registrar equipo", type="primary"):
        if not nombre_equipo.strip() or not nombre_proyecto.strip() or len(integrantes) < 1 or len(asesores) < 1:
            st.error("Faltan datos o integrantes.")
        else:
            nuevo_eq = Equipo(id=db.nuevo_id(), nombre_equipo=nombre_equipo.strip(), nombre_proyecto=nombre_proyecto.strip(), problematica=problematica.strip(), integrantes=integrantes, asesores=asesores, modalidad=modalidad, linea_proidet={"numero": num_l, "nombre": nom_l}, respuestas=respuestas, propuesta=propuesta)
            db.guardar_equipo(nuevo_eq)
            
            usuario_actual = dict(st.session_state.get("usuario_actual", {}))
            usuario_actual["equipo_id"] = nuevo_eq.id
            st.session_state["usuario_actual"] = usuario_actual
            st.session_state.pop("respuestas_inicio", None)
            st.rerun()

# ============================================================
# B) Dashboard del Alumno
# ============================================================
def _dashboard(equipo: Equipo):
    st.subheader(f"🚀 {equipo.nombre_proyecto}")
    st.caption(f"Equipo: {equipo.nombre_equipo} · {len(equipo.integrantes)} estudiantes")
    badge_etapa(equipo.etapa_actual)
    st.write("")
    progreso_etapas(equipo.etapa_actual)
    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs(["🎯 Mi proyecto", "📤 Entregables", "📚 Documentos", "📢 Avisos"])
    with tab1: _tab_proyecto(equipo)
    with tab2: _tab_entregables(equipo)
    with tab3: _tab_documentos()
    with tab4: _tab_avisos()

def _tab_proyecto(equipo: Equipo):
    st.markdown("#### 👥 Estudiantes")
    for i in equipo.integrantes: st.markdown(f"- **{i.nombre}** · {i.escuela}")
    
    st.markdown("#### 👨‍🏫 Asesores")
    for a in equipo.asesores: st.markdown(f"- **{a.nombre}**")
    
    st.markdown("#### 🧩 Problemática")
    st.write(equipo.problematica or "(sin definir)")
    
    st.divider()
    st.markdown("#### 📝 Cuestionarios por etapa")
    for bloque in ["desarrollo", "cierre"]:
        preguntas = BLOQUES_PREGUNTAS[bloque]
        with st.expander(f"{config.ETIQUETA_ETAPA[bloque]}"):
            _form_cuestionario_etapa(equipo, bloque, preguntas)

def _form_cuestionario_etapa(equipo: Equipo, bloque: str, preguntas: list):
    previas = {r.pregunta: r.respuesta for r in equipo.respuestas if r.bloque == bloque}
    with st.form(f"form_cuest_{bloque}"):
        nuevas = {}
        for i, p in enumerate(preguntas, 1):
            nuevas[p] = st.text_area(f"{i}. {p}", value=previas.get(p, ""), key=f"q_{bloque}_{i}", height=80)
        if st.form_submit_button("💾 Guardar respuestas", use_container_width=True):
            otras = [r for r in equipo.respuestas if r.bloque != bloque]
            equipo.respuestas = otras + [Respuesta(bloque=bloque, pregunta=p, respuesta=r) for p, r in nuevas.items() if r.strip()]
            db.guardar_equipo(equipo)
            st.success("Respuestas guardadas.")
            st.rerun()

def _tab_entregables(equipo: Equipo):
    entregables = db.entregables_de_equipo(equipo.id)
    if not entregables:
        mensaje_vacio("📭", "Aún no hay entregables asignados por el tutor.")
        return
    for ent in entregables:
        tarjeta_entregable(ent)
        with st.expander(f"📎 Subir PDF — {ent.titulo}"):
            _form_subir_pdf(ent)

def _form_subir_pdf(ent: Entregable):
    archivo = st.file_uploader("Selecciona el PDF", type=["pdf"], key=f"up_{ent.id}")
    if st.button("Subir", key=f"btn_up_{ent.id}"):
        if archivo is None: st.warning("Selecciona un archivo.")
        elif archivo.size > 20 * 1024 * 1024: st.error("Supera 20MB.")
        else:
            ruta = os.path.join(config.RUTA_ENTREGAS, f"{ent.id}.pdf")
            db.guardar_pdf(ruta, archivo.getbuffer().tobytes())
            ent.archivo_pdf = ruta
            ent.estado = "entregado"
            ent.fecha_entrega = datetime.now().isoformat(timespec="seconds")
            db.guardar_entregable(ent)
            st.success("¡PDF subido!")
            st.rerun()

def _tab_documentos():
    st.markdown("#### 📚 Documentos oficiales")
    docs = db.listar_documentos_publicos()
    if not docs: mensaje_vacio("📂", "No hay documentos.")
    
    for nombre in docs:
        ruta = os.path.join(config.RUTA_DOCUMENTOS, nombre)
        # --- AQUI ESTA EL TRUCO PARA QUE EL NAVEGADOR SEPA SI ES PDF O WORD ---
        mime_type = "application/pdf" if nombre.lower().endswith(".pdf") else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        with open(ruta, "rb") as f:
            st.download_button(f"⬇️ {nombre}", data=f.read(), file_name=nombre, mime=mime_type, key=f"doc_{nombre}")

def _tab_avisos():
    for a in db.get_avisos(): tarjeta_aviso(a)