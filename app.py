import pandas as pd
import streamlit as st

# 1. Configuracion de la pagina
st.set_page_config(
    page_title="Buscador de Materiales",
    layout="wide"
)

st.title("Buscador y Gestor de Materiales")
st.write("Bienvenido. Utiliza la barra de busqueda para encontrar materiales rapidamente.")

# 2. Simulacion de una base de datos de materiales
@st.cache_data
def cargar_datos():
    data = {
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
        "Stock Disponible": [120, 450, 80, 1200, 300],
        "Unidad": ["Bultos", "Varillas", "m3", "Unidades", "Metros"],
    }
    return pd.DataFrame(data)

df_materiales = cargar_datos()

# 3. Seccion de Busqueda
st.subheader("Filtro de busqueda")

# Barra de texto libre para buscar materiales
busqueda_texto = st.text_input("Escribe el nombre del material a buscar:", "")

# 4. Filtrar los datos segun la busqueda del usuario
if busqueda_texto:
    df_filtrado = df_materiales[
        df_materiales["Nombre del Material"]
        .str.contains(busqueda_texto, case=False, na=False)
    ]
else:
    df_filtrado = df_materiales

# 5. Mostrar los resultados
st.subheader("Resultados:")
if not df_filtrado.empty:
    st.dataframe(df_filtrado, use_container_width=True)
    st.success(f"Se encontraron {len(df_filtrado)} material(es).")
else:
    st.warning("No se encontro ningun material con ese nombre.")
import pandas as pd
import streamlit as st

# 1. Configuracion de la pagina
st.set_page_config(
    page_title="Buscador de Materiales",
    layout="wide"
)

st.title("Buscador y Gestor de Materiales")
st.write("Utiliza la barra de texto o sube una imagen para buscar materiales.")

# 2. Simulacion de una base de datos de materiales con referencia de imagen
@st.cache_data
def cargar_datos():
    data = {
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
        "Stock Disponible": [120, 450, 80, 1200, 300],
        "Unidad": ["Bultos", "Varillas", "m3", "Unidades", "Metros"],
        "Imagen_Referencia": ["cemento.jpg", "varilla.jpg", "arena.jpg", "ladrillo.jpg", "pvc.jpg"]
    }
    return pd.DataFrame(data)

df_materiales = cargar_datos()

# 3. Opciones de Busqueda (Texto e Imagen)
st.subheader("Filtro de busqueda")

# Pestañas para separar la busqueda por texto o por foto
pestana_texto, pestana_foto = st.tabs(["Buscar por texto", "Buscar por foto"])

df_filtrado = df_materiales.copy()

with pestana_texto:
    busqueda_texto = st.text_input("Escribe el nombre del material a buscar:", "")
    if busqueda_texto:
        df_filtrado = df_materiales[
            df_materiales["Nombre del Material"]
            .str.contains(busqueda_texto, case=False, na=False)
        ]

with pestana_foto:
    archivo_imagen = st.file_uploader("Sube una foto del material:", type=["jpg", "jpeg", "png"])
    
    if archivo_imagen is not None:
        # Mostramos la imagen cargada por el usuario
        st.image(archivo_imagen, caption="Imagen cargada para busqueda", width=300)
        
        # Aqui puedes conectar la logica de reconocimiento de imagen o filtrado por archivo.
        # Por ahora, simulamos un filtro basado en el nombre del archivo subido:
        nombre_archivo = archivo_imagen.name.lower()
        df_filtrado = df_materiales[
            df_materiales["Imagen_Referencia"].str.lower().apply(lambda x: x in nombre_archivo or nombre_archivo in x)
        ]
        
        if df_filtrado.empty:
            st.info("La imagen fue recibida, pero no se encontro una coincidencia automatica exacta con el inventario.")
            df_filtrado = df_materiales # Muestra todo si no hay coincidencia exacta simulada

# 4. Mostrar los resultados
st.subheader("Resultados:")
if not df_filtrado.empty:
    st.dataframe(df_filtrado, use_container_width=True)
    st.write(f"Se encontraron {len(df_filtrado)} material(es).")
else:
    st.warning("No se encontro ningun material con los parametros especificados.")
import pandas as pd
import streamlit as st

# 1. Configuracion de la pagina
st.set_page_config(
    page_title="Buscador y Gestor de Materiales",
    layout="wide"
)

st.title("Buscador y Gestor de Materiales")
st.write("Sistema de control de inventario de materiales.")

# 2. Base de datos simulada usando el estado de session_state para que los cambios persistan al registrar
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

df_materiales = st.session_state.df_materiales

# --- METRICAS RAPIDAS ---
st.subheader("Resumen del Inventario")
col1, col2, col3 = st.columns(3)
col1.metric("Total de Materiales", len(df_materiales))
col2.metric("Stock Total", int(df_materiales["Stock Disponible"].sum()))
# Alerta de stock bajo (menos de 50 unidades)
stock_bajo = len(df_materiales[df_materiales["Stock Disponible"] < 50])
col3.metric("Materiales con Stock Bajo", stock_bajo, delta=-stock_bajo if stock_bajo > 0 else 0, delta_color="inverse")

st.markdown("---")

# 3. Seccion de Busqueda y Gestion por pestañas principales
pestana_buscar, pestana_registrar = st.tabs(["Buscar Material", "Registrar Nuevo Material"])

with pestana_buscar:
    st.subheader("Filtro de busqueda")
    pestana_texto, pestana_foto = st.tabs(["Buscar por texto", "Buscar por foto (Simulado)"])

    df_filtrado = df_materiales.copy()

    with pestana_texto:
        busqueda_texto = st.text_input("Escribe el nombre del material a buscar:", "")
        if busqueda_texto:
            df_filtrado = df_materiales[
                df_materiales["Nombre del Material"]
                .str.contains(busqueda_texto, case=False, na=False)
            ]

    with pestana_foto:
        archivo_imagen = st.file_uploader("Sube una foto del material:", type=["jpg", "jpeg", "png"])
        if archivo_imagen is not None:
            st.image(archivo_imagen, caption="Imagen cargada para busqueda", width=300)
            nombre_archivo = archivo_imagen.name.lower()
            df_filtrado = df_materiales[
                df_materiales["Imagen_Referencia"].str.lower().apply(lambda x: x in nombre_archivo or nombre_archivo in x)
            ]
            if df_filtrado.empty:
                st.info("La imagen fue recibida. Coincidencia automatica simulada no encontrada, mostrando inventario completo.")
                df_filtrado = df_materiales

    st.subheader("Resultados:")
    if not df_filtrado.empty:
        st.dataframe(df_filtrado, use_container_width=True)
        st.write(f"Se encontraron {len(df_filtrado)} material(es).")
        
        # Seleccion de detalle de un material especifico
        st.markdown("---")
        st.subheader("Detalle del Material")
        material_seleccionado = st.selectbox("Selecciona un material para ver su detalle:", df_filtrado["Nombre del Material"].unique())
        
        if material_seleccionado:
            detalle = df_materiales[df_materiales["Nombre del Material"] == material_seleccionado].iloc[0]
            col_d1, col_d2 = st.columns(2)
            col_d1.write(f"**Codigo:** {detalle['Codigo']}")
            col_d1.write(f"**Categoria:** {detalle['Categoria']}")
            col_d2.write(f"**Stock Disponible:** {detalle['Stock Disponible']} {detalle['Unidad']}")
    else:
        st.warning("No se encontro ningun material con los parametros especificados.")

with pestana_registrar:
    st.subheader("Formulario de Registro de Material")
    with st.form("form_nuevo_material"):
        nuevo_codigo = st.text_input("Codigo del Material (Ej. M006):")
        nuevo_nombre = st.text_input("Nombre del Material:")
        nueva_categoria = st.selectbox("Categoria:", ["Construccion", "Estructura", "Aridos", "Mamposteria", "Plomeria", "Herramientas"])
        nuevo_stock = st.number_input("Stock Inicial:", min_value=0, step=1)
        nueva_unidad = st.selectbox("Unidad de Medida:", ["Bultos", "Varillas", "m3", "Unidades", "Metros", "Kilos"])
        
        boton_enviar = st.form_submit_button("Guardar Material")
        
        if boton_enviar:
            if nuevo_codigo and nuevo_nombre:
                nuevo_registro = pd.DataFrame({
                    "Codigo": [nuevo_codigo],
                    "Nombre del Material": [nuevo_nombre],
                    "Categoria": [nueva_categoria],
                    "Stock Disponible": [nuevo_stock],
                    "Unidad": [nueva_unidad],
                    "Imagen_Referencia": ["default.jpg"]
                })
                st.session_state.df_materiales = pd.concat([st.session_state.df_materiales, nuevo_registro], ignore_index=True)
                st.success(f"Material {nuevo_nombre} registrado correctamente. Ve a la pestaña de busqueda para visualizarlo.")
            else:
                st.error("Por favor completa al menos el codigo y el nombre del material.")
