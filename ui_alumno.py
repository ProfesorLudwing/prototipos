"""
ui_alumno.py — Vista del alumno en 'prototipos'.
"""
import os
from datetime import datetime
import streamlit as st

import config, db, motor_ia
from models import Respuesta, Equipo, Integrante, Asesor, Entregable
from ui_comun import header, badge_etapa, progreso_etapas, tarjeta_aviso, tarjeta_entregable, caja_info, mensaje_vacio

# Preguntas del cuestionario por etapa
BLOQUES_PREGUNTAS = {
    "inicio": ["¿Qué problema vieron en su comunidad?", "¿A quiénes afecta y desde cuándo?", "¿Cómo se resuelve hoy ese problema?", "¿Por qué la solución actual no es suficiente?", "¿Qué pasa si nadie lo resuelve en 5 años?", "¿Qué proponen hacer?", "¿Por qué es innovador frente a lo que ya existe?", "¿Qué necesitan (materiales, personas, permiso, dinero)?", "¿Cómo sabrán si funcionó?"],
    "desarrollo": ["¿Qué construyeron o probaron y qué falló?", "¿Qué cambiaron después de probar?", "¿Cómo involucraron a la comunidad?"],
    "cierre": ["¿Qué lograron y cómo lo miden?", "¿Qué harían distinto?", "¿Cómo podría servir esto a otras comunidades?"],
}

OPCION_OTRO_NOMBRE = "✏️ Otro (escribir mi propio nombre)"
LINEAS_PROIDET = [(1, "Desarrollo Tecnológico"), (2, "Investigación Educativa"), (3, "Desarrollo Sustentable y Medio Ambiente"), (4, "Investigación en Ciencias de la Salud"), (5, "Desarrollo Humano, Social y Emocional")]

# ============================================================
# Enrutador del Alumno
# ============================================================
def render(usuario: dict):
    """Decide si mostrar el cuestionario (si es nuevo) o su panel (si ya tiene equipo)."""
    header(usuario)
    equipo = db.get_equipo(usuario["equipo_id"]) if usuario.get("equipo_id") else None
    if equipo is None: 
        _vista_nuevo(usuario)
    else: 
        _dashboard(equipo)

# ============================================================
# Flujo de Registro (Alumnos nuevos)
# ============================================================
def _vista_nuevo(usuario):
    """Muestra el saludo y gestiona si ve el cuestionario o la propuesta."""
    st.subheader(f"¡Hola, {usuario['nombre']}! 👋")
    if not st.session_state.get("respuestas_inicio"): 
        _intro_y_cuestionario()
    else: 
        _propuesta_y_registro(usuario, st.session_state["respuestas_inicio"])

def _intro_y_cuestionario():
    """Muestra la caja informativa y el formulario de 9 preguntas."""
    caja_info("Antes de registrar el equipo...", "Primero van a responder un cuestionario que les ayudará a definir qué proyecto quieren hacer.")
    st.divider()
    st.markdown("### 📝 Cuestionario de inicio")
    
    # Usamos un form para que el usuario no tenga que dar clic en cada pregunta
    with st.form("form_cuestionario_inicio"):
        respuestas = {}
        for i, pregunta in enumerate(BLOQUES_PREGUNTAS["inicio"], 1):
            respuestas[pregunta] = st.text_area(f"{i}. {pregunta}", key=f"q_inicio_{i}", height=80)
        enviado = st.form_submit_button("✨ Generar propuesta", use_container_width=True)
        
    if enviado:
        # Validamos que al menos haya contestado 5 preguntas
        if len([p for p, r in respuestas.items() if not r.strip()]) > 4:
            st.error("Llenen al menos 5 respuestas.")
        else:
            st.session_state["respuestas_inicio"] = respuestas
            st.rerun()

def _propuesta_y_registro(usuario, respuestas_dict):
    """Llama a la IA para generar la propuesta y muestra el formulario de registro."""
    respuestas = [Respuesta(bloque="inicio", pregunta=p, respuesta=r) for p, r in respuestas_dict.items()]
    
    # Llamamos al motor local (sin API)
    propuesta = motor_ia.generar_propuesta(respuestas)
    sugerencias = motor_ia.sugerir_nombre_proyecto(respuestas)

    st.success("¡Cuestionario completado!")
    with st.expander("🎯 Ver propuesta generada", expanded=True):
        st.markdown(f"**Área detectada:** {propuesta['dominio_nombre']}")
        st.write(propuesta["resumen"])

    st.divider()
    st.markdown("### 🏷️ Registro del equipo")
    
    # Nombre del proyecto
    opciones = sugerencias + [OPCION_OTRO_NOMBRE]
    eleccion = st.radio("Nombre del proyecto:", opciones, key="eleccion_nombre")
    nombre_proyecto = st.text_input("Escribe el nombre del proyecto") if eleccion == OPCION_OTRO_NOMBRE else eleccion
    
    nombre_equipo = st.text_input("Nombre del equipo")
    modalidad = st.radio("Modalidad:", ["prototipo", "emprendimiento"], horizontal=True)
    
    # Línea PROIDET
    idx_linea = st.selectbox("Línea PROIDET:", options=range(len(LINEAS_PROIDET)), format_func=lambda i: f"{LINEAS_PROIDET[i][0]}. {LINEAS_PROIDET[i][1]}")
    num_l, nom_l = LINEAS_PROIDET[idx_linea]
    problematica = st.text_area("Problemática:", value=respuestas[0].respuesta, height=100)

    # Integrantes (hasta 4)
    st.markdown("**Integrantes:**")
    integrantes = []
    for i in range(4):
        c1, c2 = st.columns([3, 2])
        with c1: nom = st.text_input(f"Integrante {i+1}", value=usuario["nombre"] if i == 0 else "", key=f"int_{i}")
        with c2: esc = st.text_input("Escuela", value=config.ESCUELA, key=f"esc_{i}")
        if nom.strip(): integrantes.append(Integrante(nombre=nom.strip(), escuela=esc.strip()))

    # Asesores (1 o 2)
    st.markdown("**Asesores:**")
    tipo_asesores = st.radio("Composición:", ["dos", "uno"], format_func=lambda x: "Dos asesores" if x=="dos" else "Un solo asesor")
    asesores = []
    if tipo_asesores == "dos":
        c1, c2 = st.columns(2)
        with c1: t = st.text_input("Asesor técnico")
        with c2: m = st.text_input("Asesor metodológico")
        if t.strip(): asesores.append(Asesor(nombre=t.strip(), rol="tecnico"))
        if m.strip(): asesores.append(Asesor(nombre=m.strip(), rol="metodologico"))
    else:
        a = st.text_input("Asesor (ambas funciones)")
        if a.strip(): asesores.append(Asesor(nombre=a.strip(), rol="ambos"))

    # Guardar Equipo
    if st.button("✅ Registrar equipo", type="primary"):
        if not nombre_equipo.strip() or not nombre_proyecto.strip() or len(integrantes) < 1 or len(asesores) < 1:
            st.error("Faltan datos o integrantes.")
        else:
            nuevo_eq = Equipo(id=db.nuevo_id(), nombre_equipo=nombre_equipo.strip(), nombre_proyecto=nombre_proyecto.strip(), problematica=problematica.strip(), integrantes=integrantes, asesores=asesores, modalidad=modalidad, linea_proidet={"numero": num_l, "nombre": nom_l}, respuestas=respuestas, propuesta=propuesta)
            db.guardar_equipo(nuevo_eq)
            st.session_state["usuario_actual"]["equipo_id"] = nuevo_eq.id
            st.session_state.pop("respuestas_inicio", None)
            st.rerun()

# ============================================================
# Panel Principal del Alumno (Dashboard)
# ============================================================
def _dashboard(equipo: Equipo):
    """Muestra las 4 pestañas del alumno ya registrado."""
    st.subheader(f"🚀 {equipo.nombre_proyecto}")
    badge_etapa(equipo.etapa_actual); st.write(""); progreso_etapas(equipo.etapa_actual); st.divider()
    tab1, tab2, tab3, tab4 = st.tabs(["🎯 Mi proyecto", "📤 Entregables", "📚 Documentos", "📢 Avisos"])
    with tab1: _tab_proyecto(equipo)
    with tab2: _tab_entregables(equipo)
    with tab3: _tab_documentos()
    with tab4: _tab_avisos()

def _tab_proyecto(equipo: Equipo):
    """Muestra los datos del equipo y los cuestionarios de avance."""
    st.markdown("#### 👥 Estudiantes")
    for i in equipo.integrantes: st.markdown(f"- **{i.nombre}** · {i.escuela}")
    st.markdown("#### 👨‍🏫 Asesores")
    for a in equipo.asesores: st.markdown(f"- **{a.nombre}**")
    st.markdown("#### 🧩 Problemática")
    st.write(equipo.problematica or "(sin definir)")
    st.divider()
    st.markdown("#### 📝 Cuestionarios por etapa")
    for bloque in ["desarrollo", "cierre"]:
        with st.expander(f"{config.ETIQUETA_ETAPA[bloque]}"):
            _form_cuestionario_etapa(equipo, bloque, BLOQUES_PREGUNTAS[bloque])

def _form_cuestionario_etapa(equipo: Equipo, bloque: str, preguntas: list):
    """Formulario para que el equipo responda las preguntas de Desarrollo o Cierre."""
    previas = {r.pregunta: r.respuesta for r in equipo.respuestas if r.bloque == bloque}
    with st.form(f"form_cuest_{bloque}"):
        nuevas = {}
        for i, p in enumerate(preguntas, 1):
            nuevas[p] = st.text_area(f"{i}. {p}", value=previas.get(p, ""), key=f"q_{bloque}_{i}", height=80)
        if st.form_submit_button("💾 Guardar respuestas", use_container_width=True):
            otras = [r for r in equipo.respuestas if r.bloque != bloque]
            equipo.respuestas = otras + [Respuesta(bloque=bloque, pregunta=p, respuesta=r) for p, r in nuevas.items() if r.strip()]
            db.guardar_equipo(equipo)
            st.success("Respuestas guardadas."); st.rerun()

def _tab_entregables(equipo: Equipo):
    """Lista los entregables del equipo."""
    entregables = db.entregables_de_equipo(equipo.id)
    if not entregables:
        mensaje_vacio("📭", "Aún no hay entregables asignados por el tutor.")
        return
    for ent in entregables:
        tarjeta_entregable(ent)
        with st.expander(f"📎 Subir archivos — {ent.titulo}"):
            _form_subir_pdf(ent)

def _form_subir_pdf(ent: Entregable):
    """Permite subir múltiples archivos. Los guarda con un nombre único."""
    # accept_multiple_files=True permite elegir varios a la vez
    archivos = st.file_uploader("Selecciona PDF o Word (puedes elegir varios)", type=["pdf", "docx"], accept_multiple_files=True, key=f"up_{ent.id}")
    
    if st.button("Subir archivos", key=f"btn_up_{ent.id}"):
        if not archivos:
            st.warning("Selecciona al menos un archivo.")
        else:
            for archivo in archivos:
                if archivo.size > 20 * 1024 * 1024:
                    st.error(f"El archivo {archivo.name} supera los 20MB. Se omitirá.")
                    continue
                
                # Limpiamos el nombre y le agregamos la hora para que no se sobreescriban si suben 2 con el mismo nombre
                nombre_limpio = archivo.name.replace(" ", "_")
                nombre_guardado = f"{ent.id}_{datetime.now().strftime('%H%M%S')}_{nombre_limpio}"
                ruta = os.path.join(config.RUTA_ENTREGAS, nombre_guardado)
                
                db.guardar_pdf(ruta, archivo.getbuffer().tobytes())
                ent.archivos_pdf.append(ruta)
            
            # Cambiamos el estado y guardamos
            ent.estado = "entregado"
            ent.fecha_entrega = datetime.now().isoformat(timespec="seconds")
            db.guardar_entregable(ent)
            st.success("¡Archivos subidos exitosamente!")
            st.rerun()

def _tab_documentos():
    """Muestra los documentos oficiales para descargar."""
    st.markdown("#### 📚 Documentos oficiales")
    docs = db.listar_documentos_publicos()
    if not docs: mensaje_vacio("📂", "No hay documentos.")
    for nombre in docs:
        ruta = os.path.join(config.RUTA_DOCUMENTOS, nombre)
        # Detecta si es PDF o Word para decirle al navegador cómo abrirlo
        mime_type = "application/pdf" if nombre.lower().endswith(".pdf") else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        with open(ruta, "rb") as f:
            st.download_button(f"⬇️ {nombre}", data=f.read(), file_name=nombre, mime=mime_type, key=f"doc_{nombre}")

def _tab_avisos():
    """Muestra los avisos publicados por el tutor."""
    for a in db.get_avisos(): tarjeta_aviso(a)