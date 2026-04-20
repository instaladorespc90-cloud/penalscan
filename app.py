import streamlit as st
import hashlib

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────
st.set_page_config(
    page_title="PenalScan",
    page_icon="⚖️",
    layout="wide",
)

# ─────────────────────────────────────────
# API KEY (SECRETS + FALLBACK)
# ─────────────────────────────────────────
api_key = st.secrets.get("GOOGLE_API_KEY", "")

with st.sidebar:
    st.title("⚖️ PenalScan")

    if not api_key:
        api_key = st.text_input("Google API Key", type="password")

# ─────────────────────────────────────────
# ESTADO
# ─────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# ─────────────────────────────────────────
# FUNCIONES
# ─────────────────────────────────────────
def build_agent(api_key):

    if not api_key:
        return None

    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=api_key,
        temperature=0.1,
    )

    search_tool = DuckDuckGoSearchRun()

    prompt = ChatPromptTemplate.from_messages([
        ("system", "Sos un asistente jurídico penal argentino. Usá solo resultados reales."),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(
        llm=llm,
        tools=[search_tool],
        prompt=prompt
    )

    return AgentExecutor(
        agent=agent,
        tools=[search_tool],
        max_iterations=5,
        early_stopping_method="generate",
        handle_parsing_errors=True,
    )

# ─────────────────────────────────────────
# CHAT UI
# ─────────────────────────────────────────
st.title("⚖️ PenalScan")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Consultá jurisprudencia...")

# ─────────────────────────────────────────
# EJECUCIÓN
# ─────────────────────────────────────────
if user_input:

    if not api_key:
        st.warning("Ingresá API Key")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    history = []
    for m in st.session_state.messages[:-1]:
        if m["role"] == "user":
            history.append(HumanMessage(content=m["content"]))
        else:
            history.append(AIMessage(content=m["content"]))

    with st.chat_message("assistant"):
        with st.spinner("Buscando..."):
            try:
                agent = build_agent(api_key)

                if not agent:
                    response = "Error creando agente"
                else:
                    result = agent.invoke({
                        "input": user_input,
                        "chat_history": history
                    })
                    response = result.get("output", "Sin respuesta")

            except Exception as e:
                response = f"Error: {str(e)}"

        st.markdown(response)

    st.session_state.messages.append({
        "role": "assistant",
        "content": response
    })
