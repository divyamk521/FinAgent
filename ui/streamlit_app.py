"""
FinAgent — Streamlit Chat UI.

Run with:
    streamlit run ui/streamlit_app.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage

from agent import create_graph, invoke_graph
from config import config

st.set_page_config(page_title="FinAgent", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700&family=Inter:wght@300;400;500&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
h1, h2, h3 { font-family: 'Syne', sans-serif; }
.stApp { background: #080c10; color: #dce6ef; }
section[data-testid="stSidebar"] { background: #0e1318; border-right: 1px solid #1d2731; }
section[data-testid="stSidebar"] * { color: #dce6ef !important; }
.msg-user {
    background: #111820; border: 1px solid #1d2731;
    border-radius: 12px 12px 2px 12px; padding: 12px 16px;
    margin: 8px 0; margin-left: 15%; color: #c8ddf0;
}
.msg-ai {
    background: #0a1016; border: 1px solid #1d2731;
    border-left: 3px solid #00d084;
    border-radius: 2px 12px 12px 12px; padding: 12px 16px;
    margin: 8px 0; margin-right: 15%; color: #dce6ef;
}
.msg-label { font-size: 11px; font-weight: 500; letter-spacing: 0.08em;
    text-transform: uppercase; margin-bottom: 4px; opacity: 0.45; }
.stTextInput > div > div > input {
    background: #0e1318 !important; border: 1px solid #1d2731 !important;
    color: #dce6ef !important; border-radius: 8px !important; }
.stButton > button {
    background: #00d084 !important; color: #080c10 !important;
    border: none !important; border-radius: 8px !important; font-weight: 600 !important; }
.stButton > button:hover { opacity: 0.85 !important; }
div[data-testid="stMarkdownContainer"] p { color: #dce6ef; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📈 FinAgent")
    st.markdown("---")
    st.markdown("### 🔑 API Keys")
    groq_key = st.text_input("Groq API Key", value=config.GROQ_API_KEY, type="password",
                              help="Free at https://console.groq.com")
    finlight_key = st.text_input("Finlight API Key", value=config.FINLIGHT_API_KEY, type="password",
                                  help="Free at https://app.finlight.me")
    if groq_key:
        config.GROQ_API_KEY = groq_key
        os.environ["GROQ_API_KEY"] = groq_key
    if finlight_key:
        config.FINLIGHT_API_KEY = finlight_key

    st.markdown("### 🤖 Model")
    model = st.selectbox("Groq Model", [
        "llama-3.3-70b-versatile", "llama3-8b-8192",
        "mixtral-8x7b-32768", "gemma2-9b-it"
    ])
    config.LLM_MODEL = model

    st.markdown("### 🔬 LangSmith Tracing")
    ls_key = st.text_input("LangSmith API Key", value=config.LANGSMITH_API_KEY, type="password",
                            help="Free at https://smith.langchain.com")
    ls_project = st.text_input("Project Name", value=config.LANGSMITH_PROJECT)
    ls_enabled = st.toggle("Enable Tracing", value=config.LANGSMITH_TRACING)
    if ls_key:
        config.LANGSMITH_API_KEY  = ls_key
        config.LANGSMITH_TRACING  = ls_enabled
        config.LANGSMITH_PROJECT  = ls_project
        config.setup_langsmith()
    if ls_enabled and ls_key:
        st.success(f"Tracing → `{ls_project}`")
    elif ls_enabled and not ls_key:
        st.warning("Enter LangSmith API key to enable tracing.")

    st.markdown("---")
    st.markdown("""**Tips**
- NSE stocks → append `.NS`  
  e.g. `RELIANCE.NS`, `TCS.NS`
- US stocks → plain ticker  
  e.g. `AAPL`, `TSLA`
""")
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.session_state.graph = None
        st.rerun()

# ── Session ───────────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "graph" not in st.session_state:
    st.session_state.graph = None

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# 📊 FinAgent")
st.markdown("<span style='color:#5a7080;font-size:14px'>Groq LLM · yfinance · Finlight — all free</span>", unsafe_allow_html=True)
st.markdown("---")

# ── Quick prompts ─────────────────────────────────────────────────────────────
QUICK = ["How is Apple (AAPL) doing?", "TSLA fundamentals", "Technicals for RELIANCE.NS",
         "Latest Nvidia news", "MSFT analyst forecast"]
cols = st.columns(len(QUICK))
for col, prompt in zip(cols, QUICK):
    if col.button(prompt, use_container_width=True):
        st.session_state._quick = prompt

# ── Chat history ──────────────────────────────────────────────────────────────
for role, content in st.session_state.messages:
    label = "You" if role == "user" else "FinAgent"
    css   = "msg-user" if role == "user" else "msg-ai"
    st.markdown(f'<div class="{css}"><div class="msg-label">{label}</div>{content}</div>',
                unsafe_allow_html=True)

# ── Input form ────────────────────────────────────────────────────────────────
with st.form("chat_form", clear_on_submit=True):
    c1, c2 = st.columns([8, 1])
    user_input = c1.text_input("msg", placeholder="Ask about stocks, news, fundamentals...",
                                label_visibility="collapsed")
    submitted  = c2.form_submit_button("Send", use_container_width=True)

if hasattr(st.session_state, "_quick"):
    user_input = st.session_state._quick
    del st.session_state._quick
    submitted  = True

if submitted and user_input and user_input.strip():
    if not config.GROQ_API_KEY:
        st.error("Please enter your Groq API key in the sidebar.")
    else:
        query = user_input.strip()
        st.session_state.messages.append(("user", query))
        with st.spinner("🔍 Analysing…"):
            try:
                if st.session_state.graph is None:
                    st.session_state.graph = create_graph()
                result = invoke_graph(
                    st.session_state.graph,
                    [HumanMessage(content=query)],
                    run_name=f"streamlit: {query[:60]}",
                )
                answer = ""
                for msg in reversed(result["messages"]):
                    if isinstance(msg, AIMessage) and msg.content:
                        answer = msg.content
                        break
                st.session_state.messages.append(("assistant", answer))
            except Exception as e:
                st.session_state.messages.append(("assistant", f"⚠️ Error: {e}"))
        st.rerun()
