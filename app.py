import pandas as pd
import streamlit as st
from google import genai
from PIL import Image

# 1. Configuracion de la pagina
st.set_page_config(page_title="MAT(R)IZ", layout="wide")

# 2. Instanciar el cliente
try:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.error("Verifica la clave GEMINI_API_KEY en los secretos de Streamlit.")
    client = None

# --- PIPELINES DE IA ---
def pipeline_text_generation(texto_usuario):
    """Pipeline para procesar y enriquecer texto."""
    prompt = f"Actua como un experto en construccion. Analiza y dame un nombre corto del material junto con su contexto tecnico principal: {texto_usuario}"
    interaction = client.interactions.create(
        model="gemini-3.8-flash",
        input=prompt
    )
    return interaction.output_text.strip()

def pipeline_image_to_text(imagen_cargada):
    """Pipeline multimodal para extraer texto y contexto de imagenes."""
    interaction = client.interactions.create(
        model="gemini-3.8-flash",
        input=["Identifica este material de construccion en la imagen. Dame un nombre corto y su contexto tecnico resumido.", imagen_cargada]
    )
    return interaction.output_text.strip()

# Inicializar estructuras en la sesion
if "materiales_encontrados" not in st.session_state:
    st.session_state.materiales_encontrados = []
if "historial" not in st.session_state:
    st.session_state.historial = []
if "conexiones_red" not in st.session_state:
    st.session_state.conexiones_red = []

# --- BLOQUE 1: INTERFAZ DE BUSQUEDA ---
col_izq, col_centro, col_der = st.columns([1, 2, 1])

with col_centro:
    st.markdown("<h1 style='text-align: center;'>MAT(R)IZ</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Escribe un material o sube una foto de la que quieras saber el contexto.</p>", unsafe_allow_html=True)
    
    pestana_texto, pestana_foto = st.tabs(["Buscar por texto", "Buscar por foto"])

with col_centro:
    with pestana_texto:
        busqueda_texto = st.text_input("Escribe sobre el material que buscas:", key="input_busqueda_centro")
        if st.button("Analizar con IA (Texto)", key="btn_ia_texto") and client:
            if busqueda_texto:
                with st.spinner("Ejecutando pipeline de texto..."):
                    try:
                        resultado_ia = pipeline_text_generation(busqueda_texto)
                        
                        if resultado_ia not in st.session_state.materiales_encontrados:
                            st.session_state.materiales_encontrados.append(resultado_ia)
                        
                        termino = f"Texto: {busqueda_texto}"
                        if termino not in st.session_state.historial:
                            st.session_state.historial.insert(0, termino)
                            
                        st.success("Pipeline de texto completado.")
                    except Exception as e:
                        st.error(f"Error en el pipeline de texto: {e}")

    with pestana_foto:
        archivo_imagen = st.file_uploader("Sube una foto del material:", type=["jpg", "jpeg", "png"], key="uploader_foto_centro")
        if archivo_imagen is not None:
            img = Image.open(archivo_imagen)
            st.image(img, caption="Imagen cargada para analisis", width=250)
            
            if st.button("Analizar con IA (Foto)", key="btn_ia_foto") and client:
                with st.spinner("Ejecutando pipeline de imagen..."):
                    try:
                        resultado_ia = pipeline_image_to_text(img)
                        
                        if resultado_ia not in st.session_state.materiales_encontrados:
                            st.session_state.materiales_encontrados.append(resultado_ia)
                        
                        termino = f"Foto: {archivo_imagen.name}"
                        if termino not in st.session_state.historial:
                            st.session_state.historial.insert(0, termino)
                            
                        st.success("Pipeline de imagen completado.")
                    except Exception as e:
                        st.error(f"Error en el pipeline de imagen: {e}")

st.markdown("---")

# --- BLOQUE 2: RESULTADOS ---
st.subheader("Contexto y Materiales Encontrados por la IA")

if st.session_state.materiales_encontrados:
    for idx, mat in enumerate(st.session_state.materiales_encontrados):
        st.info(f"Elemento {idx + 1}: {mat}")
else:
    st.write("Aun no hay materiales analizados. Realiza una busqueda arriba para poblar este espacio.")

st.markdown("---")

# --- BLOQUE 3: RED DE BURBUJAS Y CONEXION MULTIPLE ---
st.subheader("Haz tus propias conexiones entre materiales")

if st.session_state.materiales_encontrados:
    burbujas_seleccionadas = st.multiselect(
        "Selecciona los elementos para vincular:",
        options=st.session_state.materiales_encontrados,
        key="multiselect_burbujas_materiales"
    )

    if st.button("Crear Red de Conexiones"):
        if len(burbujas_seleccionadas) >= 2:
            for i in range(len(burbujas_seleccionadas)):
                for j in range(i + 1, len(burbujas_seleccionadas)):
                    conexion_par = f"{burbujas_seleccionadas[i]} <---> {burbujas_seleccionadas[j]}"
                    if conexion_par not in st.session_state.conexiones_red:
                        st.session_state.conexiones_red.append(conexion_par)
            st.success("Red de conexiones creada exitosamente.")
        else:
            st.error("Selecciona al menos dos elementos para conectar.")

if st.session_state.conexiones_red:
    st.markdown("### Mapa de Relaciones Activas:")
    for rel in st.session_state.conexiones_red:
        st.code(rel, language=None)
    
    if st.button("Limpiar Red de Conexiones"):
        st.session_state.conexiones_red = []
        st.rerun()

st.markdown("---")

# --- HISTORIAL GENERAL ---
st.subheader("Historial de Consultas")
if st.session_state.historial:
    for h in st.session_state.historial[:5]:
        st.text(f"- {h}")
