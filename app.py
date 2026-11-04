import pandas as pd
import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. Configuracion de la pagina
st.set_page_config(
    page_title="Buscador y Red de Materiales con IA",
    layout="wide"
)

# 2. Configurar la API Key de forma segura desde los secretos de Streamlit
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.error("No se encontro la clave de API configurada en los secretos de Streamlit.")

# Inicializar estructuras en la sesion
if "materiales_encontrados" not in st.session_state:
    st.session_state.materiales_encontrados = []

if "historial" not in st.session_state:
    st.session_state.historial = []

if "conexiones_red" not in st.session_state:
    st.session_state.conexiones_red = []

# --- BLOQUE 1: TEXTO Y BARRA DE BUSQUEDA CENTRADOS ---
col_izq, col_centro, col_der = st.columns([1, 2, 1])

with col_centro:
    st.markdown("<h1 style='text-align: center;'>Buscador de Materiales con IA</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Ingresa un texto o sube una foto para que la IA analice el contexto del material.</p>", unsafe_allow_html=True)
    
    pestana_texto, pestana_foto = st.tabs(["Buscar por texto", "Buscar por foto"])

with col_centro:
    with pestana_texto:
        busqueda_texto = st.text_input("Escribe sobre el material que buscas:", "", key="input_busqueda_centro")
        if st.button("Analizar con IA (Texto)", key="btn_ia_texto"):
            if busqueda_texto:
                with st.spinner("La IA esta analizando el contexto..."):
                    try:
                        # CORRECCION: Usamos el modelo actual compatible con la libreria
                        model = genai.GenerativeModel('gemini-2.5-flash')
                        prompt = f"Actua como un experto en construccion y materiales. Analiza el siguiente material o consulta y dame un nombre corto del material junto con su contexto tecnico principal: {busqueda_texto}"
                        response = model.generate_content(prompt)
                        
                        resultado_ia = response.text.strip()
                        
                        if resultado_ia not in st.session_state.materiales_encontrados:
                            st.session_state.materiales_encontrados.append(resultado_ia)
                        
                        termino = f"Texto: {busqueda_texto}"
                        if termino not in st.session_state.historial:
                            st.session_state.historial.insert(0, termino)
                            
                        st.success("Analisis de texto completado.")
                    except Exception as e:
                        st.error(f"Ocurrio un error al conectar con la IA: {e}")
            else:
                st.warning("Escribe algo para que la IA pueda analizarlo.")

    with pestana_foto:
        archivo_imagen = st.file_uploader("Sube una foto del material:", type=["jpg", "jpeg", "png"], key="uploader_foto_centro")
        if archivo_imagen is not None:
            img = Image.open(archivo_imagen)
            st.image(img, caption="Imagen cargada para analisis", width=250)
            
            if st.button("Analizar con IA (Foto)", key="btn_ia_foto"):
                with st.spinner("La IA esta procesando la imagen..."):
                    try:
                        # CORRECCION: Usamos el modelo actual compatible con la libreria
                        model = genai.GenerativeModel('gemini-2.5-flash')
                        response = model.generate_content([
                            "Identifica este material de construccion en la imagen. Dame un nombre corto y su contexto tecnico resumido.",
                            img
                        ])
                        
                        resultado_ia = response.text.strip()
                        
                        if resultado_ia not in st.session_state.materiales_encontrados:
                            st.session_state.materiales_encontrados.append(resultado_ia)
                        
                        termino = f"Foto: {archivo_imagen.name}"
                        if termino not in st.session_state.historial:
                            st.session_state.historial.insert(0, termino)
                            
                        st.success("Analisis de imagen completado.")
                    except Exception as e:
                        st.error(f"Ocurrio un error al procesar la imagen con la IA: {e}")

st.markdown("---")

# --- BLOQUE 2: RESULTADOS Y CONTEXTO ENCONTRADO POR LA IA ---
st.subheader("Contexto y Materiales Encontrados por la IA")

if st.session_state.materiales_encontrados:
    for idx, mat in enumerate(st.session_state.materiales_encontrados):
        st.info(f"Elemento {idx + 1}: {mat}")
else:
    st.write("Aun no hay materiales analizados. Realiza una busqueda arriba para que la IA comience a poblar este espacio.")

st.markdown("---")

# --- BLOQUE 3: RED DE BURBUJAS Y CONEXION MULTIPLE ---
st.subheader("Red de Materiales por Burbujas")
st.write("Selecciona los materiales detectados para conectarlos entre si en una red de relaciones.")

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
else:
    st.write("Primero debes buscar materiales con la IA para poder conectarlos en la red.")

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
else:
    st.write("Sin consultas recientes.")
