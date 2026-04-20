import streamlit as st
import hashlib
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

# =============================================================================
# 1. CONFIGURACIÓN
# =============================================================================
st.set_page_config(page_title="PenalScan", page_icon="⚖️", layout="wide", initial_sidebar_state="expanded")

DARK_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] { background-color: #0d1117 !important; color: #c9d1d9 !important; font-family: 'IBM Plex Sans', sans-serif !important; }
[data-testid="stSidebar"] { background-color: #161b22 !important; border-right: 1px solid #21262d !important; }
[data-testid="stSidebar"] * { color: #c9d1d9 !important; }
.penal-header { background: linear-gradient(135deg, #0d1117 0%, #1a2332 100%); border: 1px solid #21262d; border-left: 4px solid #f0a500; border-radius: 8px; padding: 16px 20px; margin-bottom: 20px; }
.penal-header h1 { font-family: 'IBM Plex Mono', monospace !important; color: #f0a500 !important; font-size: clamp(1.4rem, 4vw, 2rem) !important; margin: 0 !important; letter-spacing: 2px; }
.penal-header p { color: #8b949e !important; font-size: 0.8rem; margin: 4px 0 0 0; font-family: 'IBM Plex Mono', monospace; }
[data-testid="stChatMessage"][data-testid*="user"] { background-color: #1c2128 !important; border: 1px solid #21262d !important; border-radius: 12px !important; }
[data-testid="stChatMessage"]:not([data-testid*="user"]) { background-color: #161b22 !important; border: 1px solid #f0a500 !important; border-radius: 12px !important; }
[data-testid="stChatInput"] textarea { background-color: #161b22 !important; color: #c9d1d9 !important; border: 2px solid #f0a500 !important; border-radius: 12px !important; }
.stButton > button { background: #f0a500 !important; color: #0d1117 !important; font-weight: 700 !important; border: none !important; border-radius: 10px !important; }
.stButton > button:hover { opacity: 0.85 !important; }
</style>
"""
st.markdown(DARK_CSS, unsafe_allow_html=True)

DEFAULT_SOURCES = "saij.gob.ar\nsj.csjn.gov.ar\nmpf.gob.ar\nscw.pjn.gov.ar\njusticia.ar\njuris.justucuman.gov.ar\njustucuman.gov.ar\n"

# =============================================================================
# 2. SIDEBAR
# =============================================================================
with st.sidebar:
    st.markdown("## ⚖️ PenalScan")
    st.markdown("---")
    st.markdown("### 🔑 Google Gemini API Key")
    api_key = st.text_input(label="API Key", type="password", placeholder="AIza...", label_visibility="collapsed", key="api_key_input")
    st.markdown("---")
    st.markdown("### 📂 Fuentes Oficiales")
    sources_text = st.text_area(label="Fuentes", value=DEFAULT_SOURCES, height=150, label_visibility="collapsed", key="sources_input")
    st.markdown("---")
    if st.button("🗑️ Limpiar Sesión"):
        st.session_state.messages = []
        st.rerun()

# =============================================================================
# 3. HEADER Y ESTADO
# =============================================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

st.markdown("""<div class="penal-header"><h1>⚖️ PENALSCAN</h1><p>ASISTENTE DE LITIGACIÓN PENAL ARGENTINA</p></div>""", unsafe_allow_html=True)

# =============================================================================
# 4. AGENTE IA
# =============================================================================
def build_agent(api_key: str, sources_raw: str):
    domains = [line.strip().lstrip("https://").lstrip("http://").rstrip("/") for line in sources_raw.splitlines() if line.strip()]
    site_filter = f"({' OR '.join(f'site:{d}' for d in domains)})" if domains else ""
    
    prompt_str = f"""Eres PenalScan, asistente penal argentino. No inventes fallos.
Paso 1: Traducir consulta a términos penales.
Paso 2: Buscar usando: {site_filter}.
Paso 3: Responder así:
---
🏛️ **[Carátula] · [Tribunal] · [Fecha]**
📝 **Hechos:** (Máximo 2 líneas)
⚖️ **Doctrina:** (Concisa)
🔗 **Enlace:** [Link directo]
---
💡 **SÍNTESIS:** <Exactamente 5 palabras>
---
Si no encuentras, di: "⚠️ Sin precedentes."."""

    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key, temperature=0.1)
    search_tool = DuckDuckGoSearchRun()
    prompt = ChatPromptTemplate.from_messages([("system", prompt_str), MessagesPlaceholder(variable_name="chat_history", optional=True), ("human", "{input}"), MessagesPlaceholder(variable_name="agent_scratchpad")])
    return AgentExecutor(agent=create_tool_calling_agent(llm=llm, tools=[search_tool], prompt=prompt), tools=[search_tool], verbose=False)

# =============================================================================
# 5. CHAT
# =============================================================================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else "⚖️"):
        st.markdown(msg["content"])

user_input = st.chat_input("Ej: Busco fallos sobre dolo eventual...")

if user_input:
    if not api_key:
        st.warning("⚠️ Ingresá tu API Key en la barra lateral.")
        st.stop()
        
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👤"): st.markdown(user_input)

    lc_history = [HumanMessage(content=m["content"]) if m["role"] == "user" else AIMessage(content=m["content"]) for m in st.session_state.messages[:-1]]

    with st.chat_message("assistant", avatar="⚖️"):
        with st.spinner("🔍 Consultando jurisprudencia..."):
            try:
                result = build_agent(api_key, sources_text).invoke({"input": user_input, "chat_history": lc_history})
                response_text = result.get("output", "Sin respuesta.")
            except Exception as e:
                response_text = f"❌ **Error:** {str(e)}"
        st.markdown(response_text)
    st.session_state.messages.append({"role": "assistant", "content": response_text})
