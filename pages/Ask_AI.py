# pages/Ask_AI.py
"""Ask AI - chat with the air-quality agent (LangGraph + Groq over the MCP tools)."""

import os
import uuid

import streamlit as st

# Bridge Streamlit secrets into the environment before importing config-using code.
try:
    for _k in ("GROQ_API_KEY", "MCP_AUTH_TOKEN", "MCP_URL", "MODEL", "LOG_LEVEL"):
        if _k in st.secrets and not os.environ.get(_k):
            os.environ[_k] = str(st.secrets[_k])
except Exception:
    pass  # no secrets file locally; rely on real env vars

from chatbot.agent import answer, build_agent  # noqa: E402
from chatbot.config import get_settings  # noqa: E402

st.set_page_config(page_title="Ask AI - Air Quality", page_icon=None, layout="wide")
st.title("Ask AI")
st.caption("Ask about AQI and pollutants across 11 Indian cities (2015-2020, historical).")


@st.cache_resource(show_spinner="Connecting to the air-quality tools...")
def _get_agent():
    return build_agent()


# Fail clearly if secrets are missing.
try:
    get_settings()
    agent = _get_agent()
except Exception as e:  # noqa: BLE001
    st.error(
        "Chatbot is not configured. Add GROQ_API_KEY and MCP_AUTH_TOKEN to "
        ".streamlit/secrets.toml (see .streamlit/secrets.toml.example).\n\n"
        f"Details: {e}"
    )
    st.stop()

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []

# Render history.
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("tool_calls"):
            with st.expander("Tools used"):
                for c in msg["tool_calls"]:
                    st.code(f"{c['name']}({c['args']})", language="python")

# Handle new input.
if prompt := st.chat_input("e.g. Which city has the worst AQI?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                result = answer(agent, st.session_state.thread_id, prompt)
                text, tool_calls = result["text"], result["tool_calls"]
                latency = result["latency_s"]
            except Exception as e:  # noqa: BLE001
                text, tool_calls, latency = f"Sorry, something went wrong: {e}", [], None
        st.markdown(text)
        if tool_calls:
            with st.expander(f"Tools used ({latency}s)" if latency else "Tools used"):
                for c in tool_calls:
                    st.code(f"{c['name']}({c['args']})", language="python")

    st.session_state.messages.append(
        {"role": "assistant", "content": text, "tool_calls": tool_calls}
    )
