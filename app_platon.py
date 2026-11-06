import json
import io
import streamlit as st
from groq import Groq
from pypdf import PdfReader
from docx import Document
from fpdf import FPDF

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

# --- FUNCIONES PARA LECTURA DE ARCHIVOS ---
def extraer_texto_pdf(file):
    pdf_reader = PdfReader(file)
    texto = ""
    for page in pdf_reader.pages:
        t = page.extract_text()
        if t:
            texto += t + "\n"
    return texto

def extraer_texto_docx(file):
    doc = Document(file)
    texto = []
    for para in doc.paragraphs:
        if para.text:
            texto.append(para.text)
    return "\n".join(texto)

# --- FUNCIONES PARA GENERACIÓN DE ARCHIVOS DE SALIDA ---
def generar_docx(contenido_texto, titulo="Reporte Platón AI"):
    doc = Document()
    doc.add_heading(titulo, level=1)
    for linea in contenido_texto.split("\n"):
        doc.add_paragraph(linea)
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

def generar_pdf(contenido_texto, titulo="Reporte Platón AI"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=14, style="B")
    pdf.cell(0, 10, txt=titulo, new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(5)
    pdf.set_font("Helvetica", size=10)
    
    texto_limpio = contenido_texto.encode('latin-1', 'replace').decode('latin-1')
    
    for linea in texto_limpio.split("\n"):
        pdf.multi_cell(0, 6, txt=linea)
    
    return bytes(pdf.output())


# Entrada universal de texto
st.subheader("Entrada de Texto")
tab_paste, tab_file = st.tabs(["Pegar texto directamente", "Cargar archivo (.txt, .docx, .pdf)"])

ensayo_texto = ""

with tab_paste:
    pasted_text = st.text_area("Pega tu ensayo o fragmento aquí:", height=180)
    if pasted_text.strip():
        ensayo_texto = pasted_text

with tab_file:
    uploaded_file = st.file_uploader(
        "Carga tu archivo de ensayo", 
        type=["txt", "docx", "pdf"]
    )
    if uploaded_file is not None:
        file_type = uploaded_file.name.split(".")[-1].lower()
        if file_type == "txt":
            ensayo_texto = uploaded_file.read().decode("utf-8")
        elif file_type == "docx":
            ensayo_texto = extraer_texto_docx(uploaded_file)
        elif file_type == "pdf":
            ensayo_texto = extraer_texto_pdf(uploaded_file)

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

def validar_ejecucion():
    if not api_key.strip():
        st.warning("Por favor ingresa tu Groq API Key en la barra lateral.")
        return False
    if not ensayo_texto.strip():
        st.warning("Por favor ingresa o carga un texto antes de ejecutar el análisis.")
        return False
    return True

# Componente reutilizable de descarga multiformato
def mostrar_botones_descarga(texto_reporte, nombre_base="reporte_platon"):
    st.subheader("📥 Exportar Resultados")
    col_d1, col_d2, col_d3 = st.columns(3)
    
    with col_d1:
        st.download_button(
            "Descargar .txt",
            data=texto_reporte,
            file_name=f"{nombre_base}.txt",
            mime="text/plain",
            use_container_width=True
        )
    with col_d2:
        docx_bytes = generar_docx(texto_reporte, titulo=nombre_base.replace("_", " ").upper())
        st.download_button(
            "Descargar Word (.docx)",
            data=docx_bytes,
            file_name=f"{nombre_base}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
    with col_d3:
        pdf_bytes = generar_pdf(texto_reporte, titulo=nombre_base.replace("_", " ").upper())
        st.download_button(
            "Descargar PDF (.pdf)",
            data=pdf_bytes,
            file_name=f"{nombre_base}.pdf",
            mime="application/pdf",
            use_container_width=True
        )


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
                
                reporte_txt = f"SÍNTESIS GENERAL:\n{res.get('resumen_general', '')}\n\nPUNTOS FUERTES:\n" + "\n".join(res.get('puntos_fuertes', [])) + "\n\nASPECTOS A MEJORAR:\n" + "\n".join(res.get('aspectos_a_mejorar', []))
                mostrar_botones_descarga(reporte_txt, nombre_base="resumen_ejecutivo_platon")


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
    "ambiguedades": [{{"fragmento": "...", "sugerencia": "..."}}],
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
                amb_textos = []
                for amb in res.get("ambiguedades", []):
                    with st.expander(f"Fragmento: \"{amb.get('fragmento', '')}\""):
                        st.write(f"**Sugerencia:** {amb.get('sugerencia', '')}")
                    amb_textos.append(f"- Fragmento: {amb.get('fragmento', '')} | Sugerencia: {amb.get('sugerencia', '')}")
                        
                st.subheader("Repeticiones o Redundancias Detectadas")
                for rep in res.get("repeticiones_muletillas", []):
                    st.markdown(f"* {rep}")

                reporte_txt = f"REGISTRO ACADÉMICO: {res.get('nivel_academico', '')}\n\nDIAGNÓSTICO:\n{res.get('diagnostico_estilo', '')}\n\nAMBIGÜEDADES:\n" + "\n".join(amb_textos)
                mostrar_botones_descarga(reporte_txt, nombre_base="analisis_redaccion_platon")


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
    "falacias_logicas": [{{"tipo": "...", "fragmento": "...", "explicacion": "..."}}],
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
                
                falacias_txt = []
                col_f, col_p = st.columns(2)
                with col_f:
                    st.subheader("Falacias Lógicas")
                    falacias = res.get("falacias_logicas", [])
                    if falacias:
                        for f in falacias:
                            with st.expander(f"Falacia: {f.get('tipo', 'N/A')}"):
                                st.markdown(f"**Fragmento:** *\"{f.get('fragmento', '')}\"*")
                                st.markdown(f"**Explicación:** {f.get('explicacion', '')}")
                            falacias_txt.append(f"- Tipo: {f.get('tipo', '')} | Fragmento: {f.get('fragmento', '')} | Razón: {f.get('explicacion', '')}")
                    else:
                        st.caption("No se detectaron falacias explícitas.")
                        
                with col_p:
                    st.subheader("Premisas sin Justificación")
                    for p_item in res.get("premisas_no_justificadas", []):
                        st.error(p_item)
                        
                    st.subheader("Saltos Lógicos")
                    for s_item in res.get("saltos_logicos", []):
                        st.warning(s_item)

                reporte_txt = f"TESIS CENTRAL:\n{res.get('tesis_central', '')}\n\nFALACIAS LÓGICAS:\n" + "\n".join(falacias_txt) + "\n\nPREMISAS SIN JUSTIFICAR:\n" + "\n".join(res.get('premisas_no_justificadas', []))
                mostrar_botones_descarga(reporte_txt, nombre_base="auditoria_argumentativa_platon")


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
                st.text_area("Resultado:", value=texto_reformulado, height=260)
                
                mostrar_botones_descarga(texto_reformulado, nombre_base="texto_reformulado_platon")
