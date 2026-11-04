import io
import re
import time
import requests
import streamlit as st
from google import genai
from google.genai import types
from PIL import Image, ImageOps

st.set_page_config(page_title="MAT(R)IZ", page_icon="🧱", layout="wide")

MODELO_PRINCIPAL = "gemini-3.5-flash-lite"
MODELO_RESPALDO = "gemini-3.8-flash"

INSTRUCCIONES = """Eres MAT(R)IZ, especialista en materiales, historia, arte y arquitectura.
Responde EXCLUSIVAMENTE en español. Crea fichas completas, claras y rigurosas.
Usa este formato Markdown, sin introducciones adicionales:
MATERIAL: nombre concreto del material
### 01. Identificación y características
Describe composición, propiedades, textura y usos.
### 02. Historia y evolución
Explica origen, civilizaciones, hitos y fechas fiables.
### 03. Arte y arquitectura
Incluye dos obras, autores o movimientos reales, con fechas aproximadas y su relación con el material.
### 04. Aplicaciones contemporáneas
Describe usos actuales en construcción, diseño y artes.
### 05. Valor cultural y simbólico
Explica el valor estético o social del material.
Extensión orientativa: 300 a 450 palabras en total. No cuentes palabras, no muestres razonamientos ni instrucciones.
No inventes autores, obras ni fechas. Cuando no estés seguro, dilo. Si una foto es ambigua, indícalo.
"""

@st.cache_resource
def obtener_cliente(clave):
    return genai.Client(api_key=clave, http_options=types.HttpOptions(timeout=30000))

try:
    client = obtener_cliente(st.secrets["GEMINI_API_KEY"])
except Exception:
    client = None
    st.error("Falta GEMINI_API_KEY en los Secrets de Streamlit.")


def consultar_gemini(contenido):
    if client is None:
        raise RuntimeError("No se ha configurado GEMINI_API_KEY.")

    configuracion = types.GenerateContentConfig(
        system_instruction=INSTRUCCIONES,
        temperature=0.3,
        max_output_tokens=3500,
    )
    try:
        respuesta = client.models.generate_content(
            model=MODELO_PRINCIPAL, contents=contenido, config=configuracion
        )
    except Exception as error:
        mensaje = str(error).lower()
        if any(x in mensaje for x in ("503", "unavailable", "404", "not found")):
            respuesta = client.models.generate_content(
                model=MODELO_RESPALDO, contents=contenido, config=configuracion
            )
        else:
            raise

    texto = (respuesta.text or "").strip()
    if not texto:
        raise RuntimeError("Gemini no devolvió contenido de texto.")
    return texto


def pipeline_text_generation(texto):
    return consultar_gemini(
        f"Investiga el siguiente material y desarrolla TODAS las secciones de la ficha: {texto}"
    )


def optimizar_imagen(imagen):
    imagen = ImageOps.exif_transpose(imagen).convert("RGB")
    imagen.thumbnail((768, 768))
    buffer = io.BytesIO()
    imagen.save(buffer, format="JPEG", quality=75, optimize=True)
    return buffer.getvalue()


def pipeline_image_to_text(imagen):
    contenido = [
        types.Part.from_bytes(data=optimizar_imagen(imagen), mime_type="image/jpeg"),
        "Identifica el material principal de la fotografía y desarrolla TODAS las secciones de la ficha. Si es dudoso, acláralo.",
    ]
    return consultar_gemini(contenido)


def extraer_nombre_material(resultado):
    coincidencia = re.search(r"(?im)^\s*(?:\*\*)?MATERIAL\s*:\s*(.+)$", resultado)
    if coincidencia:
        return coincidencia.group(1).replace("**", "").strip()[:90]
    return "Material por identificar"


@st.cache_data(ttl=86400, show_spinner=False)
def buscar_foto_material(nombre):
    equivalencias = {
        "madera": "wood texture", "ladrillo": "red brick masonry",
        "hormigón": "concrete texture", "hormigon": "concrete texture",
        "hormigón armado": "reinforced concrete", "concreto": "concrete texture",
        "acero": "steel material", "vidrio": "glass material",
        "mármol": "marble stone texture", "marmol": "marble stone texture",
        "piedra": "natural stone", "cerámica": "ceramic tiles",
        "ceramica": "ceramic tiles", "bambú": "bamboo material",
        "adobe": "adobe bricks", "yeso": "plaster material",
    }
    consulta = equivalencias.get(nombre.lower().strip(), nombre)
    parametros = {
        "action": "query", "generator": "search", "gsrsearch": consulta,
        "gsrnamespace": 6, "gsrlimit": 12, "prop": "imageinfo",
        "iiprop": "url|mime|extmetadata", "iiurlwidth": 320,
        "iiextmetadatafilter": "LicenseShortName", "format": "json",
    }
    try:
        respuesta = requests.get(
            "https://commons.wikimedia.org/w/api.php",
            params=parametros,
            headers={"User-Agent": "MatrizEducationalApp/1.0 (Streamlit; educational material reference search)"},
            timeout=8,
        )
        respuesta.raise_for_status()
        paginas = respuesta.json().get("query", {}).get("pages", {})
        for pagina in paginas.values():
            for foto in pagina.get("imageinfo", []):
                if foto.get("mime", "").startswith("image/") and foto.get("thumburl"):
                    licencia = foto.get("extmetadata", {}).get("LicenseShortName", {}).get("value", "")
                    return {"url": foto["thumburl"], "fuente": foto.get("descriptionurl", ""), "licencia": licencia}, None
        return None, f"No se encontraron imágenes para «{consulta}»."
    except (requests.RequestException, ValueError) as error:
        return None, f"La búsqueda de imágenes falló: {error}"


def mostrar_error(error):
    mensaje = str(error)
    if "429" in mensaje or "RESOURCE_EXHAUSTED" in mensaje:
        st.error("Se alcanzó el límite de solicitudes de Gemini. Revisa tu cuota.")
    elif "401" in mensaje or "403" in mensaje:
        st.error("La API rechazó la solicitud. Revisa la clave y sus permisos.")
    elif "timeout" in mensaje.lower() or "timed out" in mensaje.lower():
        st.error("Gemini tardó demasiado en responder. Inténtalo nuevamente.")
    else:
        st.error(f"Error: {mensaje}")


for variable, valor in {
    "materiales_encontrados": [], "historial": [], "conexiones_red": [],
}.items():
    if variable not in st.session_state:
        st.session_state[variable] = valor


def guardar_resultado(resultado, consulta, nombre):
    nombres = [m["nombre"] for m in st.session_state.materiales_encontrados]
    if nombre not in nombres:
        st.session_state.materiales_encontrados.append({"nombre": nombre, "texto": resultado})
    else:
        indice = nombres.index(nombre)
        st.session_state.materiales_encontrados[indice]["texto"] = resultado
    st.session_state.historial.insert(0, consulta)


col_izq, col_centro, col_der = st.columns([1, 2, 1])
with col_centro:
    st.markdown("<h1 style='text-align:center;'>MAT(R)IZ</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>Explora materiales, arte, historia y arquitectura.</p>", unsafe_allow_html=True)
    pestana_texto, pestana_foto = st.tabs(["Buscar por texto", "Buscar por foto"])

    with pestana_texto:
        busqueda_texto = st.text_input("¿Qué material quieres investigar?", placeholder="Ejemplo: ladrillo")
        if st.button("Analizar con IA (Texto)", type="primary", disabled=client is None):
            if not busqueda_texto.strip():
                st.warning("Escribe el nombre de un material.")
            else:
                with st.spinner("Investigando el material..."):
                    inicio = time.perf_counter()
                    try:
                        resultado = pipeline_text_generation(busqueda_texto.strip())
                        guardar_resultado(resultado, f"Texto: {busqueda_texto}", busqueda_texto.strip())
                        st.success("Material identificado.")
                        st.caption(f"Tiempo: {time.perf_counter() - inicio:.1f} s")
                    except Exception as error:
                        mostrar_error(error)

    with pestana_foto:
        archivo = st.file_uploader("Sube una fotografía", type=["jpg", "jpeg", "png"])
        if archivo is not None:
            try:
                imagen = Image.open(archivo)
                st.image(imagen, caption="Fotografía seleccionada", width=250)
                if st.button("Analizar con IA (Foto)", type="primary", disabled=client is None):
                    with st.spinner("Identificando material de la fotografía..."):
                        inicio = time.perf_counter()
                        try:
                            resultado = pipeline_image_to_text(imagen)
                            nombre = extraer_nombre_material(resultado)
                            guardar_resultado(resultado, f"Foto: {archivo.name}", nombre)
                            st.success("Fotografía analizada.")
                            st.caption(f"Tiempo: {time.perf_counter() - inicio:.1f} s")
                        except Exception as error:
                            mostrar_error(error)
            except (OSError, ValueError) as error:
                st.error(f"No se pudo abrir la fotografía: {error}")

st.divider()
st.subheader("Archivo de materiales MAT(R)IZ")
materiales = st.session_state.materiales_encontrados

if materiales:
    for indice, material in enumerate(materiales, start=1):
        with st.container(border=True):
            st.caption(f"FICHA {indice:03d} — {material['nombre']}")
            columna_foto, columna_texto = st.columns([1, 2], gap="large")
            with columna_foto:
                foto, error_foto = buscar_foto_material(material["nombre"])
                if foto:
                    st.image(foto["url"], caption="Fotografía de referencia", width="stretch")
                    if foto["fuente"]:
                        st.markdown(f"[Ver fuente y atribución]({foto['fuente']})")
                    if foto["licencia"]:
                        st.caption(f"Licencia: {foto['licencia']}")
                else:
                    st.caption("No se encontró una fotografía de referencia.")
                    if error_foto:
                        st.caption(error_foto)
            with columna_texto:
                st.markdown(material["texto"])
else:
    st.info("Todavía no hay materiales analizados.")

st.divider()
st.subheader("Haz tus propias conexiones entre materiales")
if materiales:
    seleccionados = st.multiselect("Selecciona al menos dos materiales:", options=[m["nombre"] for m in materiales])
    if st.button("Crear red de conexiones"):
        if len(seleccionados) < 2:
            st.warning("Selecciona al menos dos materiales.")
        else:
            for i in range(len(seleccionados)):
                for j in range(i + 1, len(seleccionados)):
                    par = tuple(sorted([seleccionados[i], seleccionados[j]]))
                    if par not in st.session_state.conexiones_red:
                        st.session_state.conexiones_red.append(par)
            st.success("Conexiones creadas.")

if st.session_state.conexiones_red:
    st.markdown("### Mapa de relaciones activas")
    for origen, destino in st.session_state.conexiones_red:
        st.write(f"🔗 {origen} ↔ {destino}")
    if st.button("Limpiar red de conexiones"):
        st.session_state.conexiones_red = []
        st.rerun()

st.divider()
st.subheader("Historial de consultas")
for consulta in st.session_state.historial[:5]:
    st.write(f"• {consulta}")
if not st.session_state.historial:
    st.caption("Aún no hay consultas.")


