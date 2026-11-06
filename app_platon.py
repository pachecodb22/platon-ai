import json
import streamlit as st
from groq import Groq

# Configuración de la página
st.set_page_config(
    page_title="Platón AI - Auditoría de Ensayos",
    page_icon="🏛️",
    layout="wide"
)

# Estilo y Título principal
st.title("🏛️ Platón AI")

st.markdown("""
**¿Qué es Platón AI?**  
Platón AI es un asistente de análisis del discurso y auditoría lógica diseñado para evaluar ensayos y textos académicos. 
A través de un procesamiento modular, extrae la estructura teórica del escrito (tesis, premisas y conclusiones) y examina su rigor argumentativo, 
identificando falacias lógicas, afirmaciones sin respaldo y saltos en la inferencia para fortalecer la calidad de tu redacción.
""")

st.divider()

# Sidebar - Configuración de API Key
st.sidebar.header("Configuración del Sistema")
api_key = st.sidebar.text_input(
    "Groq API Key:",
    type="password",
    help="Ingresa tu API Key de Groq para procesar la IA en la nube."
)

# Entrada de texto
st.subheader("1. Cargar Ensayo Académico")
tab_paste, tab_file = st.tabs(["Pegar texto directamente", "Cargar archivo .txt"])

ensayo_texto = ""

with tab_paste:
    pasted_text = st.text_area("Pega el cuerpo de tu ensayo aquí:", height=180)
    if pasted_text.strip():
        ensayo_texto = pasted_text

with tab_file:
    uploaded_file = st.file_uploader(
        "Arrastra tu ensayo en formato de texto plano", type=["txt"]
    )
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


# Función para consultar la API de Groq inspeccionando los modelos activos de la cuenta
def consultar_platon_groq(texto, opciones, api_key_val):
    instrucciones = []

    if opciones["resumen"]:
        instrucciones.append(
            '- "resumen": {"puntos_fuertes": "Aspectos logrados del ensayo", "fallas_principales": "Fallas generales"}'
        )

    if opciones["tesis"]:
        instrucciones.append('- "tesis_principal": "La hipótesis central del autor"')

    if opciones["marco"]:
        instrucciones.append('- "marco_teorico": ["Lista de autores o conceptos clave"]')

    if opciones["premisas"]:
        instrucciones.append(
            '- "premisas_clave": ["Lista de argumentos o evidencias principales"]'
        )

    if opciones["conclusion"]:
        instrucciones.append('- "conclusiones": "Cierre o hallazgos del autor"')

    if opciones["falacias"]:
        instrucciones.append(
            '- "auditoria_critica": {"falacias_logicas": [{"tipo": "...", "fragmento": "...", "explicacion": "..."}], "premisas_no_justificadas": ["..."], "saltos_logicos": ["..."]}'
        )

    instrucciones_str = "\n".join(instrucciones)

    prompt_unico = f"""Eres Platón, un auditor académico y analista lógico riguroso. Analiza el siguiente ensayo y responde ÚNICAMENTE con un objeto JSON estructurado que contenga las siguientes llaves solicitadas:

{instrucciones_str}

No incluyas explicaciones adicionales ni texto fuera del objeto JSON.

ENSAYO A ANALIZAR:
{texto}"""

    try:
        client = Groq(api_key=api_key_val.strip())
        
        # 1. Inspeccionar qué modelos de chat están realmente activos en la API Key
        modelos_disponibles = client.models.list()
        
        # Filtro estricto: solo modelos válidos de texto/chat
        modelos_chat = [
            m.id for m in modelos_disponibles.data 
            if not m.id.startswith("whisper") 
            and not m.id.startswith("llama-guard")
            and "decommissioned" not in m.id
        ]
        
        if not modelos_chat:
            st.error("No se encontraron modelos de chat activos asociados a tu API Key.")
            return None

        # 2. Ejecutar la llamada probando los modelos reales devueltos por la API
        ultimo_error = None
        for modelo_id in modelos_chat:
            try:
                response = client.chat.completions.create(
                    model=modelo_id,
                    messages=[{"role": "user", "content": prompt_unico}],
                    temperature=0.2,
                    response_format={"type": "json_object"}
                )
                content = response.choices[0].message.content
                return json.loads(content)
            except Exception as e:
                ultimo_error = e
                continue

        st.error(f"Error al procesar la solicitud con Groq: {ultimo_error}")
        return None

    except Exception as e:
        st.error(f"Error de autenticación o conexión con la API de Groq: {e}")
        return None


# Función para renderizar los resultados
def mostrar_resultados(resultado, opciones):
    st.success("Análisis completado exitosamente.")
    st.divider()

    if opciones["resumen"] and "resumen" in resultado:
        st.header("Resumen Ejecutivo")
        res = resultado["resumen"]
        r_col1, r_col2 = st.columns(2)
        r_col1.success(f"**Puntos fuertes:**\n\n{res.get('puntos_fuertes', 'N/A')}")
        r_col2.warning(f"**Aspectos a mejorar:**\n\n{res.get('fallas_principales', 'N/A')}")
        st.divider()

    col_izq, col_der = st.columns(2)

    with col_izq:
        if opciones["tesis"] and "tesis_principal" in resultado:
            st.subheader("Tesis Central")
            st.info(resultado["tesis_principal"])

        if opciones["marco"] and "marco_teorico" in resultado:
            st.subheader("Marco Teórico y Conceptos")
            marco = resultado["marco_teorico"]
            if isinstance(marco, list):
                for m in marco:
                    st.markdown(f"* {m}")
            else:
                st.write(marco)

        if opciones["premisas"] and "premisas_clave" in resultado:
            st.subheader("Premisas Clave")
            premisas = resultado["premisas_clave"]
            if isinstance(premisas, list):
                for p in premisas:
                    st.markdown(f"* {p}")
            else:
                st.write(premisas)

        if opciones["conclusion"] and "conclusiones" in resultado:
            st.subheader("Conclusión del Autor")
            st.write(resultado["conclusiones"])

    with col_der:
        if opciones["falacias"] and "auditoria_critica" in resultado:
            st.header("Auditoría Crítica")
            auditoria = resultado["auditoria_critica"]

            falacias = auditoria.get("falacias_logicas", [])
            st.subheader(f"Falacias Lógicas ({len(falacias)})")
            if falacias:
                for f in falacias:
                    with st.expander(f"Falacia: {f.get('tipo', 'No especificada')}"):
                        st.markdown(f"**Fragmento:** *\"{f.get('fragmento', '')}\"*")
                        st.markdown(f"**Razón:** {f.get('explicacion', '')}")
            else:
                st.caption("No se detectaron falacias explícitas.")

            premisas_sin_respaldo = auditoria.get("premisas_no_justificadas", [])
            if premisas_sin_respaldo:
                st.subheader(f"Premisas sin Justificación ({len(premisas_sin_respaldo)})")
                for p_item in premisas_sin_respaldo:
                    st.error(p_item)

            saltos = auditoria.get("saltos_logicos", [])
            if saltos:
                st.subheader(f"Saltos Lógicos ({len(saltos)})")
                for s_item in saltos:
                    st.warning(s_item)


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
            mostrar_resultados(resultado, opciones_seleccionadas)
