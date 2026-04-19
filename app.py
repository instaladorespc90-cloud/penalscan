# =============================================================================
# PenalScan: Asistente de Litigación Penal
# Stack: Streamlit · LangChain · Google Gemini · DuckDuckGoSearchRun
# Autor: generado con Claude — listo para producción
# =============================================================================

import streamlit as st
import hashlib
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

# ─────────────────────────────────────────────────────────────────────────────
# 1. CONFIGURACIÓN DE PÁGINA (debe ser la primera llamada a Streamlit)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PenalScan",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# 2. CSS GLOBAL — Modo oscuro forzado + diseño mobile-first
# ─────────────────────────────────────────────────────────────────────────────
DARK_CSS = """
<style>
/* ── Fuente y fondo base ── */
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');

html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background-color: #0d1117 !important;
    color: #c9d1d9 !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: #161b22 !important;
    border-right: 1px solid #21262d !important;
}
[data-testid="stSidebar"] * { color: #c9d1d9 !important; }

/* ── Header de la app ── */
.penal-header {
    background: linear-gradient(135deg, #0d1117 0%, #1a2332 100%);
    border: 1px solid #21262d;
    border-left: 4px solid #f0a500;
    border-radius: 8px;
    padding: 16px 20px;
    margin-bottom: 20px;
}
.penal-header h1 {
    font-family: 'IBM Plex Mono', monospace !important;
    color: #f0a500 !important;
    font-size: clamp(1.4rem, 4vw, 2rem) !important;
    margin: 0 !important;
    letter-spacing: 2px;
}
.penal-header p {
    color: #8b949e !important;
    font-size: 0.8rem;
    margin: 4px 0 0 0;
    font-family: 'IBM Plex Mono', monospace;
    letter-spacing: 1px;
}

/* ── Burbuja: usuario ── */
[data-testid="stChatMessage"][data-testid*="user"] {
    background-color: #1c2128 !important;
    border: 1px solid #21262d !important;
    border-radius: 12px !important;
    margin: 8px 0 !important;
}

/* ── Burbuja: asistente ── */
[data-testid="stChatMessage"]:not([data-testid*="user"]) {
    background-color: #161b22 !important;
    border: 1px solid #f0a500 !important;
    border-radius: 12px !important;
    margin: 8px 0 !important;
}

/* ── Chat input — prominente para pulgar ── */
[data-testid="stChatInput"] textarea {
    background-color: #161b22 !important;
    color: #c9d1d9 !important;
    border: 2px solid #f0a500 !important;
    border-radius: 12px !important;
    font-size: 1rem !important;
    min-height: 56px !important;
    padding: 14px !important;
    caret-color: #f0a500;
}
[data-testid="stChatInput"] textarea:focus {
    box-shadow: 0 0 0 3px rgba(240,165,0,0.25) !important;
}

/* ── Botones ── */
.stButton > button {
    background: #f0a500 !important;
    color: #0d1117 !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 10px !important;
    width: 100% !important;
    padding: 14px !important;
    font-size: 1rem !important;
    letter-spacing: 0.5px;
    transition: opacity 0.2s;
}
.stButton > button:hover { opacity: 0.85 !important; }

/* ── Inputs en sidebar ── */
[data-testid="stSidebar"] input[type="password"],
[data-testid="stSidebar"] textarea {
    background-color: #0d1117 !important;
    border: 1px solid #30363d !important;
    color: #c9d1d9 !important;
    border-radius: 8px !important;
}

/* ── Badges de estado ── */
.badge-ok   { background:#1b4332; color:#69db7c; padding:2px 8px; border-radius:20px; font-size:.75rem; }
.badge-warn { background:#5c3317; color:#ffa94d; padding:2px 8px; border-radius:20px; font-size:.75rem; }

/* ── Spinner / progress ── */
.stSpinner > div { border-top-color: #f0a500 !important; }

/* ── Separadores y markdown ── */
hr { border-color: #21262d !important; }
code { background:#21262d !important; color:#79c0ff !important; }

/* ── Scrollbar personalizado ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0d1117; }
::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }
</style>
"""
st.markdown(DARK_CSS, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 3. FUENTES OFICIALES POR DEFECTO
# ─────────────────────────────────────────────────────────────────────────────
DEFAULT_SOURCES = """\
saij.gob.ar
sj.csjn.gov.ar
mpf.gob.ar
scw.pjn.gov.ar
justicia.ar
juris.justucuman.gov.ar
justucuman.gov.ar
juba.scba.gov.ar
jurispenal.jusneuquen.gov.ar
wwwjuri.jus.mendoza.gov.ar
juristeca.jusbaires.gob.ar
justiciacordoba.gob.ar
justiciasantafe.gov.ar
juscorrientes.gov.ar
jusentrerios.gov.ar
justiciasalta.gov.ar
jusmisiones.gov.ar
justiciachaco.gov.ar
jurisprudencia.juscatamarca.gob.ar
apps1cloud.juschubut.gov.ar
jusformosa.gov.ar
jurisprudencia.justiciajujuy.gov.ar
justicia.lapampa.gob.ar
jurisprudencia.justiciasanluis.gov.ar"""

# ─────────────────────────────────────────────────────────────────────────────
# 4. SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚖️ PenalScan")
    st.markdown("---")

    # API Key
    st.markdown("### 🔑 Google Gemini API Key")
    api_key = st.text_input(
        label="API Key",
        type="password",
        placeholder="AIza...",
        label_visibility="collapsed",
        key="api_key_input",
    )
    if api_key:
        st.markdown('<span class="badge-ok">✓ API Key ingresada</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge-warn">⚠ Sin API Key</span>', unsafe_allow_html=True)

    st.markdown("---")

    # Fuentes oficiales
    st.markdown("### 📂 Fuentes Oficiales")
    st.caption("Un dominio por línea (sin https://)")
    sources_text = st.text_area(
        label="Fuentes",
        value=DEFAULT_SOURCES,
        height=220,
        label_visibility="collapsed",
        key="sources_input",
        help="El agente usará 'site:' para limitar las búsquedas a estos dominios.",
    )

    st.markdown("---")

    # Limpiar sesión
    if st.button("🗑️ Limpiar Sesión", use_container_width=True):
        st.session_state.messages = []
        st.session_state.search_cache = {}
        st.rerun()

    st.markdown("---")
    st.caption("PenalScan v1.0 · Solo para uso profesional.\nNo reemplaza asesoramiento jurídico.")

# ─────────────────────────────────────────────────────────────────────────────
# 5. ESTADO DE SESIÓN
# ─────────────────────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []          # historial de chat
if "search_cache" not in st.session_state:
    st.session_state.search_cache = {}      # caché manual de búsquedas

# ─────────────────────────────────────────────────────────────────────────────
# 6. HEADER PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="penal-header">
    <h1>⚖️ PENALSCAN</h1>
    <p>ASISTENTE DE LITIGACIÓN PENAL ARGENTINA · POWERED BY GEMINI</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 7. CACHÉ DE BÚSQUEDAS (hash de la query → resultado)
# ─────────────────────────────────────────────────────────────────────────────
def get_cache_key(query: str) -> str:
    """Genera una clave de caché determinista para la query."""
    return hashlib.md5(query.encode("utf-8")).hexdigest()


def cached_search(search_tool: DuckDuckGoSearchRun, query: str) -> str:
    """
    Ejecuta una búsqueda web con caché en session_state.
    Si la misma query ya fue ejecutada en esta sesión, devuelve el resultado
    guardado sin hacer una nueva petición (ahorra cuota y tiempo).
    """
    key = get_cache_key(query)
    if key in st.session_state.search_cache:
        return st.session_state.search_cache[key]

    result = search_tool.run(query)
    st.session_state.search_cache[key] = result
    return result

# ─────────────────────────────────────────────────────────────────────────────
# 8. CONSTRUCCIÓN DEL AGENTE LANGCHAIN
# ─────────────────────────────────────────────────────────────────────────────
def build_site_filter(sources_raw: str) -> str:
    """
    Convierte la lista de dominios de la sidebar en una cadena de operadores
    site: para usar en la búsqueda.  Ej: (site:saij.gob.ar OR site:cij.gov.ar)
    """
    domains = [
        line.strip().lstrip("https://").lstrip("http://").rstrip("/")
        for line in sources_raw.splitlines()
        if line.strip()
    ]
    if not domains:
        return ""
    parts = " OR ".join(f"site:{d}" for d in domains)
    return f"({parts})"


SYSTEM_PROMPT = """\
Eres PenalScan, un asistente de litigación penal argentina de élite.
Tu única fuente de información son los resultados de la herramienta de búsqueda web.
NUNCA inventes fallos, artículos, ni jurisprudencia. Si no encontrás resultados reales, respondé exactamente: "Sin precedentes en los sitios seleccionados."

## FLUJO OBLIGATORIO en cada consulta

### PASO 1 — Traducción jurídica
Identificá y reformulá los términos informales a su equivalente técnico penal/procesal argentino.
Ejemplos de traducción:
  - "arma de juguete" → "arma inidónea / utilería"
  - "le pegué" → "lesiones leves dolosas"
  - "me agarraron con droga" → "tenencia simple / tenencia con fines de comercialización (Ley 23.737)"
  - "lo acusan de robo a mano armada" → "robo agravado por el uso de arma (art. 166 inc. 2 CP)"

### PASO 2 — Construcción de la búsqueda
Construí una query avanzada combinando:
  a) Los términos técnicos del PASO 1.
  b) El filtro de dominios oficiales que recibirás como contexto: {site_filter}
  c) Palabras clave adicionales como: jurisprudencia, fallo, sentencia, precedente, doctrina, cámara, tribunal.

### PASO 3 — Ejecución y extracción
Ejecutá la búsqueda con la herramienta disponible. Analizá los resultados y extraé:
  - Carátula del fallo (si existe).
  - Tribunal y fecha.
  - Hechos relevantes.
  - Ratio decidendi / doctrina aplicada.
  - URL directa al fallo.

### PASO 4 — Respuesta formateada
Respondé SIEMPRE en este formato Markdown exacto (sin agregar ni quitar secciones):

---
🏛️ **[Carátula] · [Tribunal] · [Fecha]**

📝 **Hechos:** (Máximo 2 líneas. Qué ocurrió y cuál fue la imputación.)

⚖️ **Doctrina (Ratio):** (Explicación técnica concisa. Por qué el tribunal decidió como lo hizo. Cita el artículo del Código Penal o la ley especial si surge de los resultados.)

🔗 **Enlace al fallo:** [Ver fallo completo](<URL directa>)

---
💡 **SÍNTESIS:** <Exactamente 5 palabras que capturan la esencia del fallo>

---

Si encontrás MÚLTIPLES fallos relevantes, repetí el bloque anterior para cada uno (máximo 3 fallos por respuesta).
Si NO encontrás resultados concretos en los sitios oficiales, respondé solo:
> ⚠️ **Sin precedentes en los sitios seleccionados.**
> Sugerencia: ampliá los dominios en la sidebar o reformulá la consulta.

Idioma: español jurídico argentino. Nunca uses lenguaje coloquial en la respuesta final.
"""


def build_agent(api_key: str, sources_raw: str) -> AgentExecutor | None:
    """
    Construye y devuelve un AgentExecutor de LangChain con:
      - Modelo: Gemini 1.5 Flash (rápido y económico para móvil)
      - Herramienta: DuckDuckGoSearchRun
      - Prompt: SYSTEM_PROMPT con el filtro de sitios inyectado
    Devuelve None si falta la API Key.
    """
    if not api_key:
        return None

    site_filter = build_site_filter(sources_raw)

    # LLM — Gemini 1.5 Flash vía langchain-google-genai
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=api_key,
        temperature=0.1,      # respuestas deterministas y factuales
        convert_system_message_to_human=False,
    )

    # Herramienta de búsqueda web
    search_tool = DuckDuckGoSearchRun(
        name="duckduckgo_search",
        description=(
            "Busca información en la web usando DuckDuckGo. "
            "Usa operadores site: para limitar a dominios jurídicos oficiales argentinos."
        ),
    )

    tools = [search_tool]

    # Prompt del agente con soporte para historial de chat
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT.format(site_filter=site_filter)),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    # Agente con tool-calling nativo
    agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)

    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=False,           # en producción: False
        max_iterations=6,        # evita loops infinitos
        handle_parsing_errors=True,
        return_intermediate_steps=False,
    )

# ─────────────────────────────────────────────────────────────────────────────
# 9. RENDERIZADO DEL HISTORIAL DE CHAT
# ─────────────────────────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    role = msg["role"]
    with st.chat_message(role, avatar="👤" if role == "user" else "⚖️"):
        st.markdown(msg["content"])

# ─────────────────────────────────────────────────────────────────────────────
# 10. INPUT DE CHAT Y PROCESAMIENTO
# ─────────────────────────────────────────────────────────────────────────────
user_input = st.chat_input(
    placeholder="Ej: Busco fallos sobre robo agravado con arma inidónea en Tucumán...",
)

if user_input:
    # ── Validación de API Key ──────────────────────────────────────────────
    if not api_key:
        st.warning("⚠️ Ingresá tu **Google Gemini API Key** en la barra lateral para continuar.")
        st.stop()

    # ── Mostrar mensaje del usuario ────────────────────────────────────────
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    # ── Construir historial para LangChain ─────────────────────────────────
    lc_history = []
    for m in st.session_state.messages[:-1]:   # excluye el mensaje actual
        if m["role"] == "user":
            lc_history.append(HumanMessage(content=m["content"]))
        elif m["role"] == "assistant":
            lc_history.append(AIMessage(content=m["content"]))

    # ── Ejecutar agente ────────────────────────────────────────────────────
    with st.chat_message("assistant", avatar="⚖️"):
        with st.spinner("🔍 Consultando jurisprudencia oficial..."):
            try:
                agent_executor = build_agent(api_key, sources_text)

                if agent_executor is None:
                    response_text = "⚠️ Error al construir el agente. Verificá la API Key."
                else:
                    result = agent_executor.invoke({
                        "input": user_input,
                        "chat_history": lc_history,
                    })
                    response_text = result.get("output", "Sin respuesta del agente.")

            except Exception as e:
                error_str = str(e)
                # Mensajes de error user-friendly
                if "API_KEY" in error_str.upper() or "authentication" in error_str.lower():
                    response_text = "🔑 **Error de autenticación.** Verificá que la API Key de Gemini sea correcta."
                elif "quota" in error_str.lower() or "429" in error_str:
                    response_text = "⏳ **Cuota agotada.** Esperá unos segundos e intentá de nuevo."
                elif "timeout" in error_str.lower():
                    response_text = "⏱️ **Tiempo de espera agotado.** Intentá con una consulta más específica."
                else:
                    response_text = f"❌ **Error inesperado:** {error_str}"

        st.markdown(response_text)

    # ── Guardar respuesta en historial ─────────────────────────────────────
    st.session_state.messages.append({"role": "assistant", "content": response_text})

# ─────────────────────────────────────────────────────────────────────────────
# 11. MENSAJE DE BIENVENIDA (solo cuando no hay mensajes)
# ─────────────────────────────────────────────────────────────────────────────
if not st.session_state.messages:
    st.markdown("""
    <div style="
        background: #161b22;
        border: 1px dashed #30363d;
        border-radius: 12px;
        padding: 24px 28px;
        margin-top: 16px;
        text-align: center;
    ">
        <p style="font-size:2rem;margin:0;">⚖️</p>
        <h3 style="color:#f0a500;font-family:'IBM Plex Mono',monospace;margin:8px 0;">
            Listo para litigar
        </h3>
        <p style="color:#8b949e;font-size:0.9rem;margin:0 0 16px 0;">
            Consultá jurisprudencia penal argentina en tiempo real.<br>
            El agente traduce tu consulta informal a términos técnicos y busca en los 
            sitios oficiales configurados.
        </p>
        <div style="
            display:flex; gap:10px; flex-wrap:wrap; justify-content:center;
            font-size:0.8rem; color:#8b949e;
        ">
            <span style="background:#21262d;padding:6px 12px;border-radius:20px;">
                💬 "Busco fallos sobre robo con arma de juguete"
            </span>
            <span style="background:#21262d;padding:6px 12px;border-radius:20px;">
                💬 "Jurisprudencia tentativa de homicidio Tucumán 2023"
            </span>
            <span style="background:#21262d;padding:6px 12px;border-radius:20px;">
                💬 "Fallo prisión domiciliaria madre de menores"
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)
