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

# EXPANDIDOR INFORMATIVO Y GUÍA DE USO
with st.expander("ℹ️ ¿Qué es Platón AI y cómo se usa?"):
    st.markdown("""
    ### 🏛️ Sobre Platón AI
    **Platón AI** es un asistente especializado en el análisis del discurso, auditoría lógica de argumentos y reformulación de textos académicos. Desarrollada por **Daeni Pacheco**, esta aplicación se encuentra actualmente en fase de pruebas como proyecto de evaluación final para la **Microcredencial Universitaria en Inteligencia Artificial Generativa para Todos** de la **Universidad Carlos III de Madrid (UC3M)**.

    El sistema utiliza modelos de lenguaje de última generación a través del ecosistema de Groq para evaluar la consistencia retórica, detectar fallas en el razonamiento y optimizar la calidad estilística de borradores de ensayo y documentos académicos.

    ---

    ### 📖 Guía de uso paso a paso

    1. **Ingresa el texto a evaluar:**
       * **Opción A (Directa):** Ve a la pestaña *📝 Pegar texto directamente* e introduce o pega el borrador de tu ensayo.
       * **Opción B (Archivo):** Ve a la pestaña *📁 Cargar archivo* y sube tu documento en formato `.txt`, `.docx` o `.pdf`.
       * *Nota:* Platón AI permite evaluar documentos de hasta **15,000 caracteres** (~6-8 páginas) por consulta para garantizar la máxima velocidad y estabilidad.

    2. **Selecciona la función deseada:**
       * **📋 Resumen Ejecutivo:** Genera una síntesis panorámica del documento, destacando puntos fuertes, vacíos generales y conceptos clave.
       * **✍️ Análisis de Redacción:** Evalúa el registro estilístico, detecta ambigüedades sintácticas, redundancias y precisión léxica.
       * **⚖️ Auditoría Argumentativa:** Identifica la tesis central del autor, aísla falacias lógicas, premisas no justificadas y saltos inferenciales.
       * **🔄 Reformulador Académico:** Reescribe el escrito de forma orgánica y fluida, elevando el rigor terminológico y corrigiendo sesgos o fallas lógicas.

    3. **Exporta tu reporte:**
       * Al finalizar cualquier análisis, utiliza la franja inferior para descargar tus resultados estructurados en **.txt**, **Word (.docx)** o **PDF institucional**.
    """)

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
    pdf.set_margins(left=15, top=2
