
import io
import time
import requests

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

MODELO_PRINCIPAL = "gemini-3.8-flash-lite"
MODELO_RESPALDO = "gemini-3.6-flash"


INSTRUCCIONES = """
Eres MAT(R)IZ, una inteligencia artificial especializada
en materiales, arte, arquitectura, diseño e historia.

Responde siempre en español, con información clara,
precisa, interesante y académica.

Tu objetivo es crear una ficha cultural y técnica del
material identificado.

ESTRUCTURA OBLIGATORIA:

Primera línea:
MATERIAL: nombre del material

Después desarrolla estas secciones:

### 01. Contexto técnico
Explica qué es el material, su composición,
sus propiedades físicas y sus aplicaciones.
Extensión: entre 60 y 90 palabras.

### 02. Contexto histórico
Explica el origen del material, su evolución,
las civilizaciones o épocas que lo utilizaron
y su importancia en la historia.
Extensión: entre 70 y 100 palabras.

### 03. Referente artístico o arquitectónico
Menciona al menos una obra, artista, arquitecto
o movimiento que utilice el material.
Incluye el nombre, la fecha aproximada
y la relación del material con la obra.
Extensión: entre 60 y 90 palabras.

### 04. Aplicaciones contemporáneas
Explica cómo se utiliza actualmente en
arquitectura, diseño, arte o construcción.
Extensión: entre 40 y 60 palabras.

REGLAS:
- Responde exclusivamente en español.
- No escribas introducciones ni despedidas.
- Utiliza lenguaje técnico comprensible.
- Prioriza referentes artísticos reales y verificables.
- No inventes fechas, autores ni edificios.
- Si desconoces un dato histórico, dilo claramente.
- Si una imagen es ambigua, expresa la incertidumbre.
- No agregues enlaces ni fotografías inventadas.
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
        temperature=0.4,
        max_output_tokens=1100
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

@st.cache_data(ttl=86400, show_spinner=False)
def buscar_foto_material(nombre_material):

    # Sustituye esta URL por la de tu repositorio publico.
    identificacion = (
        "MatrizApp/1.0 "
        "(https://github.com/tu-usuario/tu-repositorio)"
    )

    parametros = {
        "action": "query",
        "generator": "search",
        "gsrsearch": nombre_material + " material texture",
        "gsrnamespace": 6,
        "gsrlimit": 8,
        "prop": "imageinfo",
        "iiprop": "url|mime|extmetadata",
        "iiurlwidth": 320,
        "iiextmetadatafilter": "LicenseShortName",
        "format": "json"
    }

    try:
        respuesta = requests.get(
            "https://commons.wikimedia.org/w/api.php",
            params=parametros,
            headers={"User-Agent": identificacion},
            timeout=5
        )

        respuesta.raise_for_status()
        datos = respuesta.json()

        paginas = datos.get("query", {}).get("pages", {})

        for pagina in paginas.values():
            imagenes = pagina.get("imageinfo", [])

            if not imagenes:
                continue

            info = imagenes[0]

            if not info.get("mime", "").startswith("image/"):
                continue

            miniatura = info.get("thumburl")

            if miniatura:
                licencia = info.get(
                    "extmetadata", {}
                ).get("LicenseShortName", {}).get("value", "")

                return {
                    "url": miniatura,
                    "fuente": info.get("descriptionurl", ""),
                    "licencia": licencia
                }

    except requests.RequestException:
        pass
    except ValueError:
        pass

    return None


def extraer_nombre_material(resultado):
    primera_linea = resultado.splitlines()[0].strip()

    if primera_linea.upper().startswith("MATERIAL:"):
        return primera_linea.split(":", 1)[1].strip()

    return primera_linea[:80]


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

st.subheader("Archivo de materiales MAT(R)IZ")

materiales = st.session_state.materiales_encontrados

if materiales:

    for indice, material in enumerate(materiales):

        with st.container(border=True):

            st.caption(f"FICHA {indice + 1:03d}")

            nombre = extraer_nombre_material(material)

            columna_foto, columna_texto = st.columns(
                [1, 2],
                gap="large"
            )

            with columna_foto:

                fotografia = buscar_foto_material(nombre)

                if fotografia:

                    st.image(
                        fotografia["url"],
                        width="stretch"
                    )

                    st.caption(
                        "Fotografía de referencia"
                    )

                    if fotografia["fuente"]:
                        st.markdown(
                            f"[Ver autoría y licencia]"
                            f"({fotografia['fuente']})"
                        )

                    if fotografia["licencia"]:
                        st.caption(
                            f"Licencia: {fotografia['licencia']}"
                        )

                else:
                    st.caption(
                        "No se encontró una fotografía "
                        "de referencia."
                    )

            with columna_texto:

                st.markdown(material)

else:
    st.info(
        "Todavía no hay materiales analizados. "
        "Realiza una búsqueda para comenzar."
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
