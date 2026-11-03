import pandas as pd
import streamlit as st

# 1. Configuracion de la pagina
st.set_page_config(
    page_title="Buscador de Materiales",
    layout="wide"
)

st.title("Buscador de Materiales y Contexto")
st.write("Utiliza la barra de texto o sube una foto para buscar materiales en el sistema.")

# 2. Base de datos simulada de materiales (preparada para futura integracion con IA)
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

# 3. Inicializar el historial de busquedas en la sesion
if "historial" not in st.session_state:
    st.session_state.historial = []

df_materiales = st.session_state.df_materiales

# 4. Opciones de Busqueda (Texto o Foto)
st.subheader("Filtro de busqueda")
pestana_texto, pestana_foto = st.tabs(["Buscar por texto", "Buscar por foto"])

df_filtrado = pd.DataFrame() # Inicia vacio o completo segun prefieras

with pestana_texto:
    busqueda_texto = st.text_input("Escribe el nombre del material a buscar:", "", key="input_busqueda_texto")
    
    if busqueda_texto:
        df_filtrado = df_materiales[
            df_materiales["Nombre del Material"]
            .str.contains(busqueda_texto, case=False, na=False)
        ]
        # Guardar en el historial si hay busqueda activa
        termino_busqueda = f"Texto: {busqueda_texto}"
        if termino_busqueda not in st.session_state.historial:
            st.session_state.historial.insert(0, termino_busqueda)

with pestana_foto:
    archivo_imagen = st.file_uploader("Sube una foto del material:", type=["jpg", "jpeg", "png"], key="uploader_foto")
    
    if archivo_imagen is not None:
        st.image(archivo_imagen, caption="Imagen cargada para busqueda", width=300)
        nombre_archivo = archivo_imagen.name.lower()
        
        # Simulacion de cruce por foto (aqui despues entrara la IA)
        df_filtrado = df_materiales[
            df_materiales["Imagen_Referencia"].str.lower().apply(lambda x: x in nombre_archivo or nombre_archivo in x)
        ]
        
        if df_filtrado.empty:
            st.info("Imagen procesada. No se encontro coincidencia exacta automatica, mostrando base completa.")
            df_filtrado = df_materiales
            
        termino_busqueda = f"Foto: {archivo_imagen.name}"
        if termino_busqueda not in st.session_state.historial:
            st.session_state.historial.insert(0, termino_busqueda)

# 5. Mostrar resultados de la busqueda actual
st.markdown("---")
st.subheader("Resultados de la busqueda:")

if 'busqueda_texto' in locals() and busqueda_texto or ('archivo_imagen' in locals() and archivo_imagen is not None):
    if not df_filtrado.empty:
        st.dataframe(df_filtrado, use_container_width=True)
        st.write(f"Se encontraron {len(df_filtrado)} material(es).")
    else:
        st.warning("No se encontro ningun material con los parametros especificados.")
else:
    st.info("Realiza una busqueda por texto o sube una imagen arriba para ver los resultados.")

# 6. Seccion de Historial de Busquedas
st.markdown("---")
st.subheader("Historial de busquedas recientes")
if st.session_state.historial:
    # Mostrar los ultimos 5 elementos del historial
    for item in st.session_state.historial[:5]:
        st.text(f"- {item}")
    
    if st.button("Limpiar historial"):
        st.session_state.historial = []
        st.rerun()
else:
    st.write("Aun no hay busquedas registradas en esta sesion.")
