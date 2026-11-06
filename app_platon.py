import json
import streamlit as st
from groq import Groq

# Configuración de la página
st.set_page_config(
    page_title="Platón AI - Auditoría y Redacción Académica",
    page_icon="🏛️",
    layout="wide"
)

# Estilo y Título principal
st.title("🏛️ Platón AI")
st.caption("Asistente integral de análisis del discurso, auditoría lógica y redacción académica.")

st.divider()

# Sidebar - Configuración de API Key y Navegación
st.sidebar.header("Configuración del Sistema")
api_key = st.sidebar.text_input(
    "Groq API Key:",
    type="password",
    help="Ingresa tu API Key de Groq para procesar la IA en la nube."
)

st.sidebar.divider()
st.sidebar.header("Menú de Funciones")
modulo_seleccionado = st.sidebar.radio(
    "Selecciona una sección:",
    [
        "1. Resumen Ejecutivo",
        "2. Análisis de Redacción",
        "3. Auditoría Argumentativa",
        "4. Reformulador Académico"
    ]
)

# Entrada universal de texto
st.subheader("Entrada de Texto")
tab_paste, tab_file = st.tabs(["Pegar texto directamente", "Cargar archivo .txt"])

ensayo_texto = ""

with tab_paste:
    pasted_text = st.text_area("Pega tu ensayo o fragmento aquí:", height=180)
    if pasted_text.strip():
        ensayo_texto = pasted_text

with tab_file:
    uploaded_file = st.file_uploader("Carga tu archivo en formato de texto plano", type=["txt"])
    if uploaded_file is not None:
        ensayo_texto = uploaded_file.read().decode("utf-8")

st.divider()

# Función central para consultar Groq
def consultar_groq(prompt_input, api_key_val, json_mode=True):
    try:
        client = Groq(api_key=api_key_val.strip())
        modelos_remote = client.models.list()
        
        modelos_chat = [
            m.id for m in modelos_remote.data 
            if not m.id.startswith("whisper") 
            and not m.id.startswith("llama-guard")
            and "decommissioned" not in m.id
        ]
        
        if not modelos_chat:
            st.error("No se encontraron modelos de chat activos en tu API Key.")
            return None

        for modelo_id in modelos_chat:
            try:
                kwargs = {
                    "model": modelo_id,
                    "messages": [{"role": "user", "content": prompt_input}],
                    "temperature": 0.2
                }
                if json_mode:
                    kwargs["response_format"] = {"type": "json_object"}
                    
                response = client.chat.completions.create(**kwargs)
                content = response.choices[0].message.content
                return json.loads(content) if json_mode else content
            except Exception:
                continue

        st.error("Error al procesar la solicitud con los modelos disponibles.")
        return None
    except Exception as e:
        st.error(f"Error de conexión con la API de Groq: {e}")
        return None

# Validaciones comunes
def validar_ejecucion():
    if not api_key.strip():
        st.warning("Por favor ingresa tu Groq API Key en la barra lateral.")
        return False
    if not ensayo_texto.strip():
        st.warning("Por favor ingresa un texto antes de ejecutar el análisis.")
        return False
    return True


# ==========================================
# SECCIÓN 1: RESUMEN EJECUTIVO
# ==========================================
if modulo_seleccionado == "1. Resumen Ejecutivo":
    st.header("📋 Resumen Ejecutivo y Estructura")
    st.markdown("Genera una síntesis panorámica del escrito, identificando puntos fuertes y vacíos generales.")
    
    if st.button("Generar Resumen", type="primary", use_container_width=True):
        if validar_ejecucion():
            prompt = f"""Eres Platón AI. Analiza el siguiente texto y responde ÚNICAMENTE con un objeto JSON estructurado:
{{
    "resumen_general": "Síntesis del escrito en 2-3 párrafos",
    "puntos_fuertes": ["Lista de aspectos logrados"],
    "aspectos_a_mejorar": ["Lista de vacíos o deficiencias generales"],
    "conceptos_clave": ["Términos o autores centrales"]
}}

TEXTO:
{ensayo_texto}"""
            
            with st.spinner("Procesando resumen ejecutivo..."):
                res = consultar_groq(prompt, api_key, json_mode=True)
                
            if res:
                st.subheader("Síntesis del Texto")
                st.write(res.get("resumen_general", ""))
                
                col1, col2 = st.columns(2)
                with col1:
                    st.success("**Puntos Fuertes:**")
                    for pf in res.get("puntos_fuertes", []):
                        st.markdown(f"* {pf}")
                with col2:
                    st.warning("**Aspectos a Mejorar:**")
                    for am in res.get("aspectos_a_mejorar", []):
                        st.markdown(f"* {am}")
                        
                st.subheader("Conceptos y Términos Clave")
                st.write(", ".join(res.get("conceptos_clave", [])))
                
                # Reporte descargable
                reporte_txt = f"SÍNTESIS GENERAL:\n{res.get('resumen_general', '')}\n\nPUNTOS FUERTES:\n" + "\n".join(res.get('puntos_fuertes', []))
                st.download_button("📥 Descargar Reporte (.txt)", data=reporte_txt, file_name="resumen_platon.txt", mime="text/plain")


# ==========================================
# SECCIÓN 2: ANÁLISIS DE REDACCIÓN Y ESTILO
# ==========================================
elif modulo_seleccionado == "2. Análisis de Redacción":
    st.header("✍️ Análisis de Redacción y Estilo Académico")
    st.markdown("Evalúa la precisión léxica, fluidez sintáctica, repeticiones e inconsistencias de tono.")
    
    if st.button("Analizar Redacción", type="primary", use_container_width=True):
        if validar_ejecucion():
            prompt = f"""Eres un editor académico riguroso. Analiza la redacción del texto y responde ÚNICAMENTE en formato JSON:
{{
    "diagnostico_estilo": "Evaluación del tono y registro académico",
    "ambiguedades": [{"fragmento": "...", "sugerencia": "..."}],
    "repeticiones_muletillas": ["Palabras o estructuras sobreusadas"],
    "nivel_academico": "Alto / Medio / Bajo"
}}

TEXTO:
{ensayo_texto}"""
            
            with st.spinner("Evaluando calidad sintáctica y estilística..."):
                res = consultar_groq(prompt, api_key, json_mode=True)
                
            if res:
                st.info(f"**Nivel de Registro Académico:** {res.get('nivel_academico', 'N/A')}")
                st.write(res.get("diagnostico_estilo", ""))
                
                st.subheader("Ambigüedades y Sugerencias de Mejora")
                for amb in res.get("ambiguedades", []):
                    with st.expander(f"Fragmento: \"{amb.get('fragmento', '')}\""):
                        st.write(f"**Sugerencia:** {amb.get('sugerencia', '')}")
                        
                st.subheader("Repeticiones o Redundancias Detectadas")
                for rep in res.get("repeticiones_muletillas", []):
                    st.markdown(f"* {rep}")


# ==========================================
# SECCIÓN 3: AUDITORÍA ARGUMENTATIVA
# ==========================================
elif modulo_seleccionado == "3. Auditoría Argumentativa":
    st.header("⚖️ Auditoría Argumentativa y Falacias Lógicas")
    st.markdown("Examina el rigor lógico del escrito, aislando falacias, premisas sin justificar y saltos inferenciales.")
    
    if st.button("Ejecutar Auditoría Lógica", type="primary", use_container_width=True):
        if validar_ejecucion():
            prompt = f"""Eres Platón, auditor académico. Analiza el ensayo y responde ÚNICAMENTE en JSON:
{{
    "tesis_central": "La hipótesis principal del autor",
    "falacias_logicas": [{"tipo": "...", "fragmento": "...", "explicacion": "..."}],
    "premisas_no_justificadas": ["..."],
    "saltos_logicos": ["..."]
}}

TEXTO:
{ensayo_texto}"""
            
            with st.spinner("Realizando auditoría lógica en Groq..."):
                res = consultar_groq(prompt, api_key, json_mode=True)
                
            if res:
                st.subheader("Tesis Central Detectada")
                st.info(res.get("tesis_central", ""))
                
                col_f, col_p = st.columns(2)
                with col_f:
                    st.subheader("Falacias Lógicas")
                    falacias = res.get("falacias_logicas", [])
                    if falacias:
                        for f in falacias:
                            with st.expander(f"Falacia: {f.get('tipo', 'N/A')}"):
                                st.markdown(f"**Fragmento:** *\"{f.get('fragmento', '')}\"*")
                                st.markdown(f"**Explicación:** {f.get('explicacion', '')}")
                    else:
                        st.caption("No se detectaron falacias explícitas.")
                        
                with col_p:
                    st.subheader("Premisas sin Justificación")
                    for p_item in res.get("premisas_no_justificadas", []):
                        st.error(p_item)
                        
                    st.subheader("Saltos Lógicos")
                    for s_item in res.get("saltos_logicos", []):
                        st.warning(s_item)


# ==========================================
# SECCIÓN 4: REFORMULADOR ACADÉMICO
# ==========================================
elif modulo_seleccionado == "4. Reformulador Académico":
    st.header("🔄 Reformulador de Texto Académico")
    st.markdown("Reescribe pasajes para elevar su rigor terminológico o corregir fallas de argumentación.")
    
    estilo_reform = st.selectbox(
        "Selecciona el enfoque de reescritura:",
        ["Formato Académico Riguroso (Formal)", "Conciso y Directo", "Eliminación de Falacias / Mayor Neutralidad"]
    )
    
    if st.button("Reformular Texto", type="primary", use_container_width=True):
        if validar_ejecucion():
            prompt = f"""Reescribe el siguiente texto con un enfoque de '{estilo_reform}'. 
Conserva la idea central, elimina sesgos, mejora la precisión léxica y devuelve la propuesta reescrita en texto plano continuo.

TEXTO A REFORMULAR:
{ensayo_texto}"""
            
            with st.spinner("Reformulando borrador..."):
                texto_reformulado = consultar_groq(prompt, api_key, json_mode=False)
                
            if texto_reformulado:
                st.subheader("Propuesta Reformulada")
                st.text_area("Resultado:", value=texto_reformulado, height=220)
                
                st.download_button(
                    "📥 Descargar Texto Reformulado (.txt)",
                    data=texto_reformulado,
                    file_name="texto_reformulado_platon.txt",
                    mime="text/plain"
                )
