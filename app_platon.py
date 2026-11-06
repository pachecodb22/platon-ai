import streamlit as st
import json
import urllib.request
import urllib.error

# Configuración de la página
st.set_page_config(
    page_title="Platón AI - Auditoría de Ensayos",
    page_icon="🏛️",
    layout="wide"
)

# Estilo y Título principal
st.title("🏛️ Platón AI")

# Breve resumen explicativo
st.markdown("""
**¿Qué es Platón AI?**  
Platón AI es un asistente de análisis del discurso y auditoría lógica diseñado para evaluar ensayos y textos académicos. 
A través de un procesamiento modular, extrae la estructura teórica del escrito (tesis, premisas y conclusiones) y examina su rigor argumentativo, 
identificando falacias lógicas, afirmaciones sin respaldo y saltos en la inferencia para fortalecer la calidad de tu redacción.
""")

st.divider()

# Sidebar - Configuración de API Key en la Nube
st.sidebar.header("Configuración del Sistema")
api_key = st.sidebar.text_input("Groq API Key:", type="password", help="Ingresa tu API Key de Groq para procesar la IA en la nube.")

# Entrada de texto
st.subheader("1. Cargar Ensayo Académico")
tab_paste, tab_file = st.tabs(["Pegar texto directamente", "Cargar archivo .txt"])

ensayo_texto = ""

with tab_paste:
    pasted_text = st.text_area("Pega el cuerpo de tu ensayo aquí:", height=180)
    if pasted_text.strip():
        ensayo_texto = pasted_text

with tab_file:
    uploaded_file = st.file_uploader("Arrastra tu ensayo en formato de texto plano", type=["txt"])
    if uploaded_file is not None:
        ensayo_texto = uploaded_file.read().decode("utf-8")

st.divider()

# Casillas de Selección
st.subheader("2. Selecciona los análisis que deseas realizar")
st.caption("Nota: Seleccionar solo los análisis requeridos optimizará el tiempo de respuesta del sistema.")

col_sel1, col_sel2 = st.columns(2)

with col_sel1:
    chk_resumen = st.checkbox("Resumen (Puntos fuertes y fallas generales)", value=True)
    chk_tesis = st.checkbox("Tesis Central", value=True)
    chk_marco = st.checkbox("Marco Teórico y Conceptos Clave", value=False)

with col_sel2:
    chk_premisas = st.checkbox("Premisas Clave", value=False)
    chk_conclusion = st.checkbox("Conclusión del Autor", value=False)
    chk_falacias = st.checkbox("Falacias y Argumentación Crítica", value=True)

# Función para consultar la API de Groq en la nube
def consultar_platon_groq(texto, opciones, api_key_val):
    instrucciones = []

    if opciones["resumen"]:
        instrucciones.append('- "resumen": {"puntos_fuertes": "Breve párrafo con los aspectos logrados del ensayo", "fallas_principales": "Breve párrafo con las fallas generales"}')

    if opciones["tesis"]:
        instrucciones.append('- "tesis_principal": "La proposición o hipótesis central del autor"')

    if opciones["marco"]:
        instrucciones.append('- "marco_teorico": ["Lista de autores, teorías o conceptos principales"]')

    if opciones["premisas"]:
        instrucciones.append('- "premisas_clave": ["Lista de argumentos o evidencias principales utilizados"]')

    if opciones["conclusion"]:
        instrucciones.append('- "conclusiones": "Hallazgos o cierre planteado por el autor"')

    if opciones["falacias"]:
        instrucciones.append('- "auditoria_critica": {"falacias_logicas": [{"tipo": "...", "fragmento": "...", "explicacion": "..."}], "premisas_no_justificadas": ["..."], "saltos_logicos": ["..."]}')

    instrucciones_str = "\n".join(instrucciones)

    system_prompt = f"""
    Eres Platón, un auditor académico y analista lógico riguroso. Tu tarea es analizar un ensayo académico y devolver un objeto JSON válido conteniendo ÚNICAMENTE las siguientes claves solicitadas:

    {instrucciones_str}

    IMPORTANTE: Responde ÚNICAMENTE con el objeto JSON estrictamente formateado. No agregues texto introductorio, ni explicaciones fuera del JSON.
    """

    url = "https://api.groq.com/openai/v1/chat/completions"
    
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analiza el siguiente ensayo:\n\n{texto}"}
        ],
        "temperature": 0.2
    }

    data = json.dumps(payload).encode('utf-8')
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key_val.strip()}',
        'User-Agent': 'Mozilla/5.0'
    }

    req = urllib.request.Request(url, data=data, headers=headers)

    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode('utf-8')
            res_json = json.loads(res_body)
            content = res_json["choices"][0]["message"]["content"]
            
            # Limpiar posible marcado Markdown si la API devuelve ```json ... ```
            content_clean = content.strip()
            if content_clean.startswith("```json"):
                content_clean = content_clean[7:]
            if content_clean.startswith("```"):
                content_clean = content_clean[3:]
            if content_clean.endswith("```"):
                content_clean = content_clean[:-3]
                
            return json.loads(content_clean.strip())
    except urllib.error.HTTPError as e:
        st.error(f"Error HTTP ({e.code}) al consultar Groq. Verifica la validez de tu API Key.")
        return None
    except Exception as e:
        st.error(f"Error procesando la solicitud: {e}")
        return None

st.divider()

# Botón de Procesamiento
if st.button("Analizar Selección con Platón", type="primary", use_container_width=True):
    opciones_seleccionadas = {
        "resumen": chk_resumen,
        "tesis": chk_tesis,
        "marco": chk_marco,
        "premisas": chk_premisas,
        "conclusion": chk_conclusion,
        "falacias": chk_falacias
    }

    if not api_key.strip():
        st.warning("Por favor ingresa tu Groq API Key en la barra lateral izquierda.")
    elif not any(opciones_seleccionadas.values()):
        st.warning("Por favor marca al menos una casilla de análisis antes de ejecutar Platón.")
    elif not ensayo_texto.strip():
        st.warning("Por favor ingresa o carga un ensayo antes de iniciar el análisis.")
    else:
        with st.spinner("Platón está procesando los módulos en la nube a través de Groq..."):
            resultado = consultar_platon_groq(ensayo_texto, opciones_seleccionadas, api_key)

        if resultado:
            st.success("Análisis completado exitosamente.")
            st.divider()

            if chk_resumen and "resumen" in resultado:
                st.header("Resumen Ejecutivo")
                res = resultado["resumen"]
                r_col1, r_col2 = st.columns(2)
                with r_col1:
                    st.success(f"**Puntos fuertes:**\n\n{res.get('puntos_fuertes', 'N/A')}")
                with r_col
