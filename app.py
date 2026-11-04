
import io
import time

import streamlit as st
from google import genai
from google.genai import types
from PIL import Image, ImageOps


# ==========================================
# CONFIGURACION GENERAL
# ==========================================

st.set_page_config(
    page_title="MAT(R)IZ",
    page_icon="🧱",
    layout="wide"
)

MODELO_PRINCIPAL = "gemini-3.5-flash-lite"
MODELO_RESPALDO = "gemini-3.6-flash"

INSTRUCCIONES = """
Eres MAT(R)IZ, una inteligencia artificial especializada
en materiales de construccion y arquitectura.

REGLAS OBLIGATORIAS:
1. Responde siempre en español.
2. Identifica el material con su nombre tecnico.
3. Agrega un contexto tecnico de maximo 15 palabras.
4. No escribas introducciones ni despedidas.
5. No uses listas ni explicaciones extensas.
6. Utiliza este formato:
Nombre del material — descripcion tecnica.
7. Si no puedes identificarlo, indica que no hay
informacion suficiente.
"""


# ==========================================
# CONEXION CON GEMINI
# ==========================================

@st.cache_resource
def obtener_cliente(api_key):
    return genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            timeout=20000
        )
    )


try:
    api_key = st.secrets["GEMINI_API_KEY"]
    client = obtener_cliente(api_key)
except Exception:
    client = None
    st.error(
        "No se pudo configurar Gemini. "
        "Revisa GEMINI_API_KEY en Streamlit Secrets."
    )


# ==========================================
# FUNCION GENERAL DE INTELIGENCIA ARTIFICIAL
# ==========================================

def consultar_gemini(contenido):
    if client is None:
        raise RuntimeError(
            "La conexion con Gemini no esta configurada."
        )

    configuracion = types.GenerateContentConfig(
        system_instruction=INSTRUCCIONES,
        temperature=0.2,
        max_output_tokens=120
    )

    try:
        respuesta = client.models.generate_content(
            model=MODELO_PRINCIPAL,
            contents=contenido,
            config=configuracion
        )

    except Exception as error:
        mensaje = str(error).lower()

        # Solo cambiar de modelo cuando el error
        # parece relacionado con disponibilidad.
        if any(codigo in mensaje for codigo in
               ["503", "unavailable", "404", "not found"]):

            respuesta = client.models.generate_content(
                model=MODELO_RESPALDO,
                contents=contenido,
                config=configuracion
            )
        else:
            raise

    if not respuesta.text or not respuesta.text.strip():
        raise RuntimeError(
            "Gemini no devolvio una respuesta de texto."
        )

    return respuesta.text.strip()


# ==========================================
# PIPELINE DE TEXTO
# ==========================================

def pipeline_text_generation(texto_usuario):

    prompt = (
        "Identifica el siguiente material de construccion "
        "y explica brevemente sus propiedades: "
        f"{texto_usuario}"
    )

    return consultar_gemini(prompt)


# ==========================================
# OPTIMIZACION DE IMAGEN
# ==========================================

def optimizar_imagen(imagen):

    imagen = ImageOps.exif_transpose(imagen)
    imagen = imagen.convert("RGB")

    # Reducimos el tamaño para acelerar el envio.
    imagen.thumbnail((768, 768))

    buffer = io.BytesIO()

    imagen.save(
        buffer,
        format="JPEG",
        quality=75,
        optimize=True
    )

    return buffer.getvalue()


# ==========================================
# PIPELINE DE IMAGEN
# ==========================================

def pipeline_image_to_text(imagen):

    imagen_bytes = optimizar_imagen(imagen)

    contenido = [
        types.Part.from_bytes(
            data=imagen_bytes,
            mime_type="image/jpeg"
        ),
        (
            "Identifica el principal material de "
            "construccion visible en esta fotografia. "
            "Responde en español y explica brevemente "
            "sus caracteristicas tecnicas."
        )
    ]

    return consultar_gemini(contenido)


# ==========================================
# MANEJO DE ERRORES
# ==========================================

def mostrar_error(error):

    mensaje = str(error)
    mensaje_lower = mensaje.lower()

    if "429" in mensaje_lower or "resource_exhausted" in mensaje_lower:
        st.error(
            "Se alcanzo el limite de solicitudes de Gemini. "
            "Revisa la cuota de tu API."
        )

    elif "403" in mensaje_lower or "401" in mensaje_lower:
        st.error(
            "Gemini rechazo la solicitud. "
            "Verifica los permisos y la clave API."
        )

    elif "timeout" in mensaje_lower or "timed out" in mensaje_lower:
        st.error(
            "Gemini supero el tiempo de espera. "
            "Intenta nuevamente."
        )

    elif "503" in mensaje_lower:
        st.error(
            "El servicio de Gemini esta temporalmente "
            "sobrecargado."
        )

    else:
        st.error(f"Error durante el analisis: {mensaje}")


# ==========================================
# VARIABLES DE SESION
# ==========================================

if "materiales_encontrados" not in st.session_state:
    st.session_state.materiales_encontrados = []

if "historial" not in st.session_state:
    st.session_state.historial = []

if "conexiones_red" not in st.session_state:
    st.session_state.conexiones_red = []


def guardar_resultado(resultado, consulta):

    if resultado not in st.session_state.materiales_encontrados:
        st.session_state.materiales_encontrados.append(resultado)

    st.session_state.historial.insert(0, consulta)


# ==========================================
# INTERFAZ PRINCIPAL
# ==========================================

col_izq, col_centro, col_der = st.columns([1, 2, 1])

with col_centro:

    st.markdown(
        "<h1 style='text-align:center;'>MAT(R)IZ</h1>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<p style='text-align:center;'>"
        "Explora, identifica y conecta materiales "
        "de construccion con inteligencia artificial."
        "</p>",
        unsafe_allow_html=True
    )

    pestana_texto, pestana_foto = st.tabs([
        "Buscar por texto",
        "Buscar por foto"
    ])

    # ======================================
    # BUSQUEDA POR TEXTO
    # ======================================

    with pestana_texto:

        busqueda_texto = st.text_input(
            "Escribe el material que deseas analizar:",
            placeholder="Ejemplo: hormigon, madera, acero..."
        )

        if st.button(
            "Analizar con IA (Texto)",
            type="primary",
            disabled=client is None
        ):

            if not busqueda_texto.strip():
                st.warning("Escribe un material primero.")

            else:
                with st.spinner("Identificando material..."):

                    inicio = time.perf_counter()

                    try:
                        resultado = pipeline_text_generation(
                            busqueda_texto.strip()
                        )

                        guardar_resultado(
                            resultado,
                            f"Texto: {busqueda_texto}"
                        )

                        duracion = time.perf_counter() - inicio

                        st.success("Material identificado.")
                        st.info(resultado)
                        st.caption(
                            f"Tiempo de respuesta: {duracion:.2f} s"
                        )

                    except Exception as error:
                        mostrar_error(error)

    # ======================================
    # BUSQUEDA POR FOTOGRAFIA
    # ======================================

    with pestana_foto:

        archivo_imagen = st.file_uploader(
            "Sube una fotografia:",
            type=["jpg", "jpeg", "png"]
        )

        if archivo_imagen is not None:

            try:
                imagen = Image.open(archivo_imagen)

                st.image(
                    imagen,
                    caption="Imagen seleccionada",
                    width=250
                )

                if st.button(
                    "Analizar con IA (Foto)",
                    type="primary",
                    disabled=client is None
                ):

                    with st.spinner("Analizando imagen..."):

                        inicio = time.perf_counter()

                        try:
                            resultado = pipeline_image_to_text(
                                imagen
                            )

                            guardar_resultado(
                                resultado,
                                f"Foto: {archivo_imagen.name}"
                            )

                            duracion = time.perf_counter() - inicio

                            st.success("Imagen analizada.")
                            st.info(resultado)
                            st.caption(
                                f"Tiempo de respuesta: {duracion:.2f} s"
                            )

                        except Exception as error:
                            mostrar_error(error)

            except Exception as error:
                st.error(f"Error al abrir la imagen: {error}")


# ==========================================
# MATERIALES ENCONTRADOS
# ==========================================

st.divider()

st.subheader("Contexto y materiales encontrados por la IA")

materiales = st.session_state.materiales_encontrados

if materiales:

    for indice, material in enumerate(materiales):

        with st.container(border=True):
            st.markdown(f"**Elemento {indice + 1}**")
            st.write(material)

else:
    st.info(
        "Todavia no hay materiales analizados. "
        "Realiza una busqueda para comenzar."
    )


# ==========================================
# CONEXIONES ENTRE MATERIALES
# ==========================================

st.divider()

st.subheader("Haz tus propias conexiones entre materiales")

if materiales:

    seleccionados = st.multiselect(
        "Selecciona los materiales que deseas conectar:",
        options=materiales
    )

    if st.button("Crear red de conexiones"):

        if len(seleccionados) < 2:

            st.warning(
                "Selecciona al menos dos materiales."
            )

        else:

            for i in range(len(seleccionados)):
                for j in range(i + 1, len(seleccionados)):

                    par = tuple(sorted([
                        seleccionados[i],
                        seleccionados[j]
                    ]))

                    if par not in st.session_state.conexiones_red:
                        st.session_state.conexiones_red.append(par)

            st.success("Conexiones creadas correctamente.")


if st.session_state.conexiones_red:

    st.markdown("### Mapa de relaciones activas")

    for material_a, material_b in st.session_state.conexiones_red:
        st.write(f"🔗 {material_a} ↔ {material_b}")

    if st.button("Limpiar red de conexiones"):
        st.session_state.conexiones_red = []
        st.rerun()


# ==========================================
# HISTORIAL
# ==========================================

st.divider()

st.subheader("Historial de consultas")

if st.session_state.historial:

    for consulta in st.session_state.historial[:5]:
        st.write(f"• {consulta}")

else:
    st.caption("Todavia no hay consultas registradas.")
