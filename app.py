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

# Inicializar historial y conexiones en la sesion
if "historial" not in st.session_state:
    st.session_state.historial = []

if "conexiones_red" not in st.session_state:
    st.session_state.conexiones_red = []

df_materiales = st.session_state.df_materiales

# --- BLOQUE 1: TEXTO Y BARRA DE BUSQUEDA CENTRADOS ---
col_izq, col_centro, col_der = st.columns([1, 2, 1])

with col_centro:
    st.markdown("<h1 style='text-align: center;'>Buscador de Materiales</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Utiliza el buscador por texto o sube una foto.</p>", unsafe_allow_html=True)
    
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

# --- BLOQUE 2: RESULTADOS DE LA BUSQUEDA ---
st.subheader("Resultados de la Busqueda")

if busqueda_activa:
    if not df_filtrado.empty:
        st.dataframe(df_filtrado, use_container_width=True)
    else:
        st.warning("No se encontraron resultados.")
else:
    st.info("Realiza una busqueda arriba para desplegar los materiales.")

st.markdown("---")

# --- BLOQUE 3: AREA DE BURBUJAS Y CONEXION MULTIPLE ---
st.subheader("Red de Materiales por Burbujas")
st.write("Selecciona varios materiales en forma de burbujas para conectarlos todos entre si en una red de relaciones.")

lista_materiales_nombres = df_materiales["Nombre del Material"].tolist()

# Selector multiple que genera burbujas o chips visuales limpios
burbujas_seleccionadas = st.multiselect(
    "Selecciona los materiales que deseas vincular:",
    options=lista_materiales_nombres,
    key="multiselect_burbujas_materiales"
)

if st.button("Crear Red de Conexiones"):
    if len(burbujas_seleccionadas) >= 2:
        # Generar todas las combinaciones posibles entre las burbujas seleccionadas
        for i in range(len(burbujas_seleccionadas)):
            for j in range(i + 1, len(burbujas_seleccionadas)):
                conexion_par = f"{burbujas_seleccionadas[i]} <---> {burbujas_seleccionadas[j]}"
                if conexion_par not in st.session_state.conexiones_red:
                    st.session_state.conexiones_red.append(conexion_par)
        st.success("Red de conexiones creada exitosamente entre las burbujas seleccionadas.")
    else:
        st.error("Debes seleccionar al menos dos materiales para crear conexiones.")

# Mostrar la red de conexiones activas
if st.session_state.conexiones_red:
    st.markdown("### Mapa de Relaciones Activas:")
    for rel in st.session_state.conexiones_red:
        st.code(rel, language=None)
    
    if st.button("Limpiar Red de Conexiones"):
        st.session_state.conexiones_red = []
        st.rerun()
else:
    st.write("Aun no hay relaciones creadas en la red.")

st.markdown("---")

# --- HISTORIAL GENERAL ---
st.subheader("Historial de Consultas")
if st.session_state.historial:
    for h in st.session_state.historial[:5]:
        st.text(f"- {h}")
else:
    st.write("Sin consultas recientes.")
