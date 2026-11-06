import json
import io
import streamlit as st
from groq import Groq
from pypdf import PdfReader
from docx import Document
from fpdf import FPDF

# Configuración del límite de caracteres para la API (aprox. 3.000 palabras / 6-8 páginas)
MAX_CARACTERES = 15000

# 1. Configuración global de la página
st.set_page_config(
    page_title="Platón AI - Auditoría y Redacción Académica",
    page_icon="🏛️",
    layout="wide"
)

# Obtener la API Key global desde los Secrets de Streamlit
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")

# 2. BARRA SUPERIOR DE TÍTULO (HEADER)
st.markdown("# 🏛️ Platón AI")
st.markdown("**Asistente integral de análisis del discurso, auditoría lógica y redacción académica.**")

if GROQ_API_KEY:
    st.caption("🟢 Sistema conectado mediante API Key institucional.")
else:
    st.error("🔴 Error: No se detectó la clave GROQ_API_KEY en los Secrets.")

st.divider()

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

# --- CLASE Y FUNCIÓN PARA GENERACIÓN DE PDF ESTRUCTURADO Y ATRACTIVO ---
class PDFReporte(FPDF):
    def header(self):
        # Franja superior institucional
        self.set_fill_color(31, 41, 55)  # Azul noche / Gris oscuro
        self.rect(0, 0, 210, 20, style="F")
        self.set_font("Helvetica", style="B", size=12)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, txt="Platon AI | Reporte de Auditoria y Redaccion Academica", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(10)

    def footer(self):
        # Pie de página con numeración
        self.set_y(-15)
        self.set_font("Helvetica", size=8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, txt=f"Pagina {self.page_no()} | Generado automaticamente por Platon AI", align="C")

def generar_docx(contenido_texto, titulo="Reporte Platón AI"):
    doc = Document()
    doc.add_heading(titulo, level=1)
    for linea in contenido_texto.split("\n"):
        doc.add_paragraph(linea)
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

def generar_pdf(contenido_texto, titulo="REPORTE DE ANÁLISIS"):
    pdf = PDFReporte(orientation="P", unit="mm", format="A4")
    pdf.set_margins(left=15, top=25, right=15)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    
    ancho_util = pdf.epw
    
    # Título principal del reporte
    titulo_limpio = titulo.encode('latin-1', 'replace').decode('latin-1').upper()
    pdf.set_font("Helvetica", style="B", size=16)
    pdf.set_text_color(17, 24, 39)
    pdf.cell(w=0, h=10, txt=titulo_limpio, align="L", new_x="LMARGIN", new_y="NEXT")
    
    # Línea decorativa inferior
    pdf.set_draw_color(59, 130, 246)  # Azul acento
    pdf.set_line_width(0.8)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(6)
    
    # Procesamiento del cuerpo por bloques
    lineas = contenido_texto.replace("\t", "    ").split("\n")
    
    for linea in lineas:
        linea_limpia = linea.encode('latin-1', 'replace').decode('latin-1').strip()
        
        if not linea_limpia:
            pdf.ln(3)
            continue
            
        # Detección de encabezados de sección para aplicar cajas de contraste
        if any(linea_limpia.startswith(sub) for sub in [
            "TESIS CENTRAL:", "SISTESIS GENERAL:", "SÍNTESIS GENERAL:", 
            "REGISTRO ACADEMICO:", "REGISTRO ACADÉMICO:", 
            "FALACIAS LOGICAS:", "FALACIAS LÓGICAS:", 
            "ASPECTOS A MEJORAR:", "PUNTOS FUERTES:", "DIAGNOSTICO:", "DIAGNÓSTICO:",
            "PREMISAS SIN JUSTIFICAR:", "AMBIGUEDADES:", "AMBIGÜEDADES:"
        ]):
            pdf.ln(4)
            pdf.set_fill_color(243, 244, 246)  # Fondo gris claro
            pdf.set_font("Helvetica", style="B", size=11)
            pdf.set_text_color(31, 41, 55)
            pdf.multi_cell(w=ancho_util, h=8, txt=f"  {linea_limpia}", fill=True, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
        # Viñetas o puntos destacados
        elif linea_limpia.startswith("- ") or linea_limpia.startswith("* "):
            pdf.set_font("Helvetica", size=10)
            pdf.set_text_color(55, 65, 81)
            pdf.multi_cell(w=ancho_util, h=5, txt=f"   * {linea_limpia[2:]}", new_x="LMARGIN", new_y="NEXT")
        # Texto estándar
        else:
            pdf.set_font("Helvetica", size=10)
            pdf.set_text_color(55, 65, 81)
            pdf.multi_cell(w=ancho_util, h=5.5, txt=linea_limpia, new_x="LMARGIN", new_y="NEXT")
            
    return bytes(pdf.output())


# 3. ENTRADA UNIVERSAL DE TEXTO
st.header("1. Cargar o Pegar Ensayo")
st.caption(f"ℹ️ **Límite de procesamiento:** Platón AI analiza hasta un máximo de **{MAX_CARACTERES:,} caracteres** (~6-8 páginas) por consulta para garantizar estabilidad.")

tab_paste, tab_file = st.tabs(["📝 Pegar texto directamente", "📁 Cargar archivo (.txt, .docx, .pdf)"])

ensayo_texto = ""

with tab_paste:
    pasted_text = st.text_area("Pega el borrador de tu ensayo aquí:", height=180)
    if pasted_text.strip():
        ensayo_texto = pasted_text

with tab_file:
    uploaded_file = st.file_uploader(
        "Arrastra tu archivo aquí", 
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

# Indicador de estado y truncado si excede el máximo
texto_procesable = ensayo_texto
if len(ensayo_texto) > 0:
    st.write(f"📊 **Caracteres detectados:** {len(ensayo_texto):,} / {MAX_CARACTERES:,}")
    if len(ensayo_texto) > MAX_CARACTERES:
        st.warning(f"⚠️ El documento excede el límite recomendado ({len(ensayo_texto):,} caracteres). Platón AI procesará únicamente los primeros {MAX_CARACTERES:,} caracteres para el análisis.")
        texto_procesable = ensayo_texto[:MAX_CARACTERES]

st.divider()

# --- FUNCIÓN CENTRAL CONSULTA GROQ ---
def consultar_groq(prompt_input, json_mode=True):
    if not GROQ_API_KEY:
        st.error("No se ha configurado la clave API de Groq en los Secrets de la aplicación.")
        return None
        
    try:
        client = Groq(api_key=GROQ_API_KEY.strip())
        modelos_remote = client.models.list()
        
        modelos_chat = [
            m.id for m in modelos_remote.data 
            if not m.id.startswith("whisper") 
            and not m.id.startswith("llama-guard")
            and "decommissioned" not in m.id
        ]
        
        if not modelos_chat:
            st.error("No se encontraron modelos de chat activos en el sistema.")
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

        st.error("Error al procesar la solicitud con los modelos disponibles. Intenta recortar el fragmento.")
        return None
    except Exception as e:
        st.error(f"Error de conexión con el servicio en la nube: {e}")
        return None

def validar_ejecucion():
    if not texto_procesable.strip():
        st.warning("Por favor ingresa o carga un texto antes de ejecutar el análisis.")
        return False
    return True

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


# 4. BARRA DE FUNCIONES HORIZONTAL (PESTAÑAS)
st.header("2. Funciones de Auditoría y Redacción")

tab_resumen, tab_redaccion, tab_auditoria, tab_reformulador = st.tabs([
    "📋 Resumen Ejecutivo",
    "✍️ Análisis de Redacción",
    "⚖️ Auditoría Argumentativa",
    "🔄 Reformulador Académico"
])

# ------------------------------------------
# PESTAÑA 1: RESUMEN EJECUTIVO
# ------------------------------------------
with tab_resumen:
    st.markdown("Genera una síntesis panorámica del escrito, identificando puntos fuertes y vacíos generales.")
    
    if st.button("Generar Resumen", type="primary", use_container_width=True, key="btn_resumen"):
        if validar_ejecucion():
            prompt = f"""Eres Platón AI. Analiza el siguiente texto y responde ÚNICAMENTE con un objeto JSON estructurado:
{{
    "resumen_general": "Síntesis del escrito en 2-3 párrafos",
    "puntos_fuertes": ["Lista de aspectos logrados"],
    "aspectos_a_mejorar": ["Lista de vacíos o deficiencias generales"],
    "conceptos_clave": ["Términos o autores centrales"]
}}

TEXTO:
{texto_procesable}"""
            
            with st.spinner("Procesando resumen ejecutivo..."):
                res = consultar_groq(prompt, json_mode=True)
                
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

# ------------------------------------------
# PESTAÑA 2: ANÁLISIS DE REDACCIÓN
# ------------------------------------------
with tab_redaccion:
    st.markdown("Evalúa la precisión léxica, fluidez sintáctica, repeticiones e inconsistencias de tono.")
    
    if st.button("Analizar Redacción", type="primary", use_container_width=True, key="btn_redaccion"):
        if validar_ejecucion():
            prompt = f"""Eres un editor académico riguroso. Analiza la redacción del texto y responde ÚNICAMENTE en formato JSON:
{{
    "diagnostico_estilo": "Evaluación del tono y registro académico",
    "ambiguedades": [{{"fragmento": "...", "sugerencia": "..."}}],
    "repeticiones_muletillas": ["Palabras o estructuras sobreusadas"],
    "nivel_academico": "Alto / Medio / Bajo"
}}

TEXTO:
{texto_procesable}"""
            
            with st.spinner("Evaluando calidad sintáctica y estilística..."):
                res = consultar_groq(prompt, json_mode=True)
                
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

# ------------------------------------------
# PESTAÑA 3: AUDITORÍA ARGUMENTATIVA
# ------------------------------------------
with tab_auditoria:
    st.markdown("Examina el rigor lógico del escrito, aislando falacias, premisas sin justificar y saltos inferenciales.")
    
    if st.button("Ejecutar Auditoría Lógica", type="primary", use_container_width=True, key="btn_auditoria"):
        if validar_ejecucion():
            prompt = f"""Eres Platón, auditor académico. Analiza el ensayo y responde ÚNICAMENTE en JSON:
{{
    "tesis_central": "La hipótesis principal del autor",
    "falacias_logicas": [{{"tipo": "...", "fragmento": "...", "explicacion": "..."}}],
    "premisas_no_justificadas": ["..."],
    "saltos_logicos": ["..."]
}}

TEXTO:
{texto_procesable}"""
            
            with st.spinner("Realizando auditoría lógica en el servidor..."):
                res = consultar_groq(prompt, json_mode=True)
                
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

# ------------------------------------------
# PESTAÑA 4: REFORMULADOR ACADÉMICO
# ------------------------------------------
with tab_reformulador:
    st.markdown("Reescribe el texto de forma orgánica, elevando su registro estilístico y solucionando deficiencias lógicas.")
    
    estilo_reform = st.selectbox(
        "Selecciona el enfoque de reescritura:",
        [
            "Eliminación de Falacias y Rigor Académico (Recomendado)",
            "Formato Académico Formal y Elegante",
            "Síntesis Concisa y Directa"
        ]
    )
    
    if st.button("Reformular Texto", type="primary", use_container_width=True, key="btn_reformulador"):
        if validar_ejecucion():
            prompt_reformulacion = f"""Eres un editor y redactor académico de nivel doctoral. 

Instrucciones de reescritura:
1. Lee el siguiente contenido y extrae ÚNICAMENTE el cuerpo argumentativo o el texto del ensayo.
2. IGNORA explícitamente cualquier metadato, encabezado de prueba, números de página, notas de pie o marcadores de archivo (por ejemplo: "Documento de prueba...", "Página X de Y", "Nota de auditoría...").
3. Reescribe el borrador de manera completamente ORGÁNICA y FLUIDA bajo un enfoque de '{estilo_reform}'.
4. Asegúrate de conectar las ideas con transiciones naturales, eliminar sesgos ad hominem o generalizaciones apresuradas, y elevar la precisión terminológica.
5. Devuelve EXCLUSIVAMENTE el texto reescrito en párrafos académicos continuos, sin introducciones del tipo "Aquí está la versión reformulada:" ni comentarios adicionales.

TEXTO FUENTE:
{texto_procesable}"""
            
            with st.spinner("Reescribiendo borrador de forma orgánica..."):
                texto_reformulado = consultar_groq(prompt_reformulacion, json_mode=False)
                
            if texto_reformulado:
                st.subheader("Propuesta Reformulada")
                st.write(texto_reformulado)
                
                mostrar_botones_descarga(texto_reformulado, nombre_base="texto_reformulado_platon")
