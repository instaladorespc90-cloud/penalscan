import sys
import subprocess
import streamlit as st

# =============================================================================
# 1. CONFIGURACIÓN DE PÁGINA (Debe ir obligatoriamente primero)
# =============================================================================
st.set_page_config(
    page_title="PenalScan",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# 2. AUTO-INSTALADOR DEFINITIVO (Solución al ImportError)
# =============================================================================
try:
    # Intenta importar la librería que estaba fallando
    from langchain.agents import AgentExecutor
except ImportError:
    # Si falla, la instala a la fuerza en tiempo real
    st.error("⚠️ El servidor no cargó las dependencias. Forzando instalación manual...")
    with st.spinner("Descargando inteligencia jurídica (esto tomará unos 60 segundos)..."):
        subprocess.check_call([sys.executable, "-m", "pip", "install", 
            "langchain", "langchain-core", "langchain-community", 
            "langchain-google-genai", "google-generativeai", 
            "duckduckgo-search", "httpx", "pydantic"
        ])
    st.success("✅ Instalación completada. Reiniciando el sistema...")
    st.rerun()

# =============================================================================
# 3. IMPORTACIONES RESTANTES (Solo llega acá si ya se instaló todo)
# =============================================================================
import hashlib
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_tool_calling_agent
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

# =============================================================================
# 4. CSS GLOBAL — Modo oscuro forzado + diseño mobile-first
# =============================================================================
DARK_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background-color: #0d1117 !important;
    color: #c9d1d9 !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
}
[data-testid="stSidebar"] {
    background-color: #161b22 !important;
    border-right: 1px solid #21262d !important;
}
[data-testid="stSidebar"] * { color: #c9d1d9 !important; }
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
}
[data-testid="stChatMessage"][data-testid*="user"] {
    background-color: #1c2128 !important;
    border: 1px solid #21262d !important;
    border-radius: 12px !important;
}
[data-testid="stChatMessage"]:not([data-testid*="user"]) {
    background-color: #161b22 !important;
    border: 1px solid #f0a500 !important;
    border-radius: 12px !important;
}
[data-testid="stChatInput"] textarea {
    background-color: #161b22 !important;
    color: #c9d1d9 !important;
    border: 2px solid #f0a500 !important;
    border-radius: 12px !important;
}
.stButton > button {
    background: #f0a500 !important;
    color: #0d1117 !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 10px !important;
}
.stButton > button:hover { opacity: 0.85 !important; }
</style>
"""
st.markdown(DARK_CSS, unsafe_allow_html=True)

# =============================================================================
# 5. FUENTES OFICIALES POR DEFECTO
# =============================================================================
DEFAULT_SOURCES = """\
saij.gob.ar
sj.csjn.gov.ar
mpf.gob.ar
scw.pjn.gov.ar
justicia.ar
juris.justucuman.gov.ar
justucuman.gov.ar
"""

# =============================================================================
# 6. SIDEBAR
# =============================================================================
with st.sidebar:
    st.markdown("## ⚖️ PenalScan")
    st.markdown("---")
    st.markdown("### 🔑 Google Gemini API Key")
    api_key = st.text_input(
        label="API Key", type="password", placeholder="AIza...",
        label_visibility="collapsed", key="api_key_input"
    )
    st.markdown("---")
    st.markdown("### 📂 Fuentes Oficiales")
    sources_text = st.text_area(
        label="Fuentes", value=DEFAULT_SOURCES, height=150,
        label_visibility="collapsed", key="sources_input"
    )
    st.markdown("---")
    if st.button("🗑️ Limpiar Sesión"):
        st.session_state.messages = []
        st.session_state.search_cache = {}
        st.rerun()

# =============================================================================
# 7. ESTADO Y HEADER
# =============================================================================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "search_cache" not in st.session_state:
    st.session_state.search_cache = {}

st.markdown("""
<div class="penal-header">
    <h1>⚖️ PENALSCAN</h1>
    <p>ASISTENTE DE LITIGACIÓN PENAL ARGENTINA</p>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# 8. LÓGICA DEL AGENTE
# =============================================================================
def build_site_filter(sources_raw: str) -> str:
    domains = [line.strip().lstrip("https://").lstrip("http://").rstrip("/")
               for line in sources_raw.splitlines() if line.strip()]
    return f"({' OR '.join(f'site:{d}' for d in domains)})" if domains else ""

SYSTEM_PROMPT = """\
Eres PenalScan, un asistente de litigación penal argentina de élite.
Tu única fuente de información son los resultados de la búsqueda web. No inventes fallos.
Paso 1: Traducir la consulta informal a términos penales argentinos (ej: arma de juguete -> arma inidónea).
Paso 2: Buscar combinando los términos con estos sitios: {site_filter}.
Paso 3: Responder en este formato estricto:

---
🏛️ **[Carátula] · [Tribunal] · [Fecha]**
📝 **Hechos:** (Máximo 2 líneas)
⚖️ **Doctrina (Ratio):** (Breve y concisa)
🔗 **Enlace al fallo:** [Link directo]
---
💡 **SÍNTESIS:** <Exactamente 5 palabras>
---
Si no encuentras nada, di: "⚠️ Sin precedentes en los sitios seleccionados."
"""

def build_agent(api_key: str, sources_raw: str):
    site_filter = build_site_filter(sources_raw)
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash", google_api_key=api_key, temperature=0.1,
        convert_system_message_to_human=False
    )
    search_tool = DuckDuckGoSearchRun()
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT.format(site_filter=site_filter)),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    agent = create_tool_calling_agent(llm=llm, tools=[search_tool], prompt=prompt)
    return AgentExecutor(agent=agent, tools=[search_tool], verbose=False)

# =============================================================================
# 9. CHAT PRINCIPAL
# =============================================================================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else "⚖️"):
        st.markdown(msg["content"])

user_input = st.chat_input("Ej: Busco fallos sobre robo agravado en Tucumán...")

if user_input:
    if not api_key:
        st.warning("⚠️ Ingresá tu API Key en la barra lateral.")
        st.stop()
        
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    lc_history = [HumanMessage(content=m["content"]) if m["role"] == "user" else AIMessage(content=m["content"]) 
                  for m in st.session_state.messages[:-1]]

    with st.chat_message("assistant", avatar="⚖️"):
        with st.spinner("🔍 Consultando jurisprudencia..."):
            try:
                agent_executor = build_agent(api_key, sources_text)
                result = agent_executor.invoke({"input": user_input, "chat_history": lc_history})
                response_text = result.get("output", "Sin respuesta.")
            except Exception as e:
                response_text = f"❌ **Error:** {str(e)}"
        st.markdown(response_text)
    st.session_state.messages.append({"role": "assistant", "content": response_text})

if not st.session_state.messages:
    st.info("💡 **Tip:** Pega tu API Key a la izquierda y escribí un tema legal abajo para empezar.")
