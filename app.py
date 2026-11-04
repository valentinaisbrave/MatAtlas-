import pandas as pd
import streamlit as st

# 1. Configuracion de la pagina
st.set_page_config(
    page_title="Buscador y Red de Materiales",
    layout="wide"
)

# 2. Base de datos simulada de materiales
if "df_materiales" not in st.session_state:
    st.session_state.df_materiales = pd.DataFrame({
        "Codigo": ["M001", "M002", "M003", "M004", "M005"],
        "Nombre del Material": [
            "Cemento Polycemento",
            "Varilla Corrugada 3/8",
            "Arena de Rio",
            "Ladrillo H10",
            "Tuberia PVC 2 pulgadas",
        ],
        "Categoria": [
            "Construccion",
            "Estructura",
            "Aridos",
            "Mamposteria",
            "Plomeria",
        ],
        "Stock Disponible": [120, 450, 30, 1200, 15],
        "Unidad": ["Bultos", "Varillas", "m3", "Unidades", "Metros"],
        "Imagen_Referencia": ["cemento.jpg", "varilla.jpg", "arena.jpg", "ladrillo.jpg", "pvc.jpg"]
    })

# Inicializar el historial y las conexiones en la sesion
if "historial" not in st.session_state:
    st.session_state.historial = []

if "conexiones" not in st.session_state:
    st.session_state.conexiones = []

df_materiales = st.session_state.df_materiales

# --- BLOQUE 1: TEXTO Y BARRA DE BUSQUEDA CENTRADOS ---
# Usamos tres columnas para dejar un espacio a los lados y centrar el contenido en la del medio
col_izq, col_centro, col_der = st.columns([1, 2, 1])

with col_centro:
    st.markdown("<h1 style='text-align: center;'>Buscador de Materiales</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Utiliza el buscador por texto o sube una foto.</p>", unsafe_allow_html=True)
    
    # Pestañas de busqueda dentro del bloque central
    pestana_texto, pestana_foto = st.tabs(["Buscar por texto", "Buscar por foto"])

df_filtrado = pd.DataFrame()
busqueda_activa = False

with col_centro:
    with pestana_texto:
        busqueda_texto = st.text_input("Escribe el nombre del material:", "", key="input_busqueda_centro")
        if busqueda_texto:
            df_filtrado = df_materiales[
                df_materiales["Nombre del Material"]
                .str.contains(busqueda_texto, case=False, na=False)
            ]
            busqueda_activa = True
            termino = f"Texto: {busqueda_texto}"
            if termino not in st.session_state.historial:
                st.session_state.historial.insert(0, termino)

    with pestana_foto:
        archivo_imagen = st.file_uploader("Sube una foto del material:", type=["jpg", "jpeg", "png"], key="uploader_foto_centro")
        if archivo_imagen is not None:
            st.image(archivo_imagen, caption="Imagen cargada", width=250)
            nombre_archivo = archivo_imagen.name.lower()
            df_filtrado = df_materiales[
                df_materiales["Imagen_Referencia"].str.lower().apply(lambda x: x in nombre_archivo or nombre_archivo in x)
            ]
            if df_filtrado.empty:
                df_filtrado = df_materiales
            busqueda_activa = True
            termino = f"Foto: {archivo_imagen.name}"
            if termino not in st.session_state.historial:
                st.session_state.historial.insert(0, termino)

st.markdown("---")

# --- BLOQUE 2: RESULTADOS DE LA BUSQUEDA (DEBAJO DE LA BUSQUEDA) ---
st.subheader("Resultados de la Busqueda")

if busqueda_activa:
    if not df_filtrado.empty:
        st.dataframe(df_filtrado, use_container_width=True)
    else:
        st.warning("No se encontraron resultados.")
else:
    st.info("Realiza una busqueda arriba para desplegar los materiales.")

st.markdown("---")

# --- BLOQUE 3: AREA DE VINCULOS Y RED DE MATERIALES (MAS ABAJO) ---
st.subheader("Espacio de Vinculos y Relaciones")
st.write("Selecciona dos materiales para crear un vinculo o conexion entre ellos en esta sesion.")

lista_materiales_nombres = df_materiales["Nombre del Material"].tolist()

col_v1, col_v2, col_v3 = st.columns(3)
with col_v1:
    material_origen = st.selectbox("Material A:", lista_materiales_nombres, key="Mat_A")
with col_v2:
    material_destino = st.selectbox("Material B:", lista_materiales_nombres, key="Mat_B")
with col_v3:
    st.write("") # Espaciador vertical
    st.write("")
    crear_vinculo = st.button("Conectar Materiales")

if crear_vinculo:
    if material_origen != material_destino:
        nuevo_vinculo = f"{material_origen} conectado con {material_destino}"
        if nuevo_vinculo not in st.session_state.conexiones:
            st.session_state.conexiones.append(nuevo_vinculo)
            st.success("Vinculo creado exitosamente.")
    else:
        st.error("No puedes conectar un material consigo mismo.")

# Mostrar los vinculos creados en forma de red o lista flotante
if st.session_state.conexiones:
    st.markdown("### Mapa de Conexiones Activas:")
    for conexion in st.session_state.conexiones:
        st.code(conexion, language=None)
else:
    st.write("Aun no hay vinculos creados entre los materiales.")

st.markdown("---")

# --- HISTORIAL GENERAL ---
st.subheader("Historial de Consultas")
if st.session_state.historial:
    for h in st.session_state.historial[:5]:
        st.text(f"- {h}")
else:
    st.write("Sin consultas recientes.")
