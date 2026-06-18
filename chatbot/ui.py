# chatbot/ui.py
"""Shared Streamlit chat UI for the Ask AI page.

One cached agent (process-wide), the full-page chat, and a "how this assistant works"
panel that lists the live MCP tools.
"""

from __future__ import annotations

import os
import uuid

import streamlit as st

from chatbot.agent import answer, build_agent, tools_info

HF_SPACE_URL = "https://huggingface.co/spaces/Bhuvandesai/india-air-quality"


def _bridge_secrets() -> None:
    """Copy Streamlit secrets into the environment (config reads from os.environ)."""
    try:
        for k in ("GROQ_API_KEY", "MCP_AUTH_TOKEN", "MCP_URL", "MODEL", "LOG_LEVEL"):
            if k in st.secrets and not os.environ.get(k):
                os.environ[k] = str(st.secrets[k])
    except Exception:  # noqa: BLE001
        pass  # no secrets file locally; rely on real env vars


@st.cache_resource(show_spinner="Connecting to the air-quality tools...")
def _get_agent():
    # Cached process-wide: exactly one agent (and one MCP connection) is shared across
    # every session and every page. It is never rebuilt per page.
    return build_agent()


def ensure_agent():
    """Return the shared agent, or show a clear setup message and stop the page."""
    _bridge_secrets()
    try:
        return _get_agent()
    except Exception as e:  # noqa: BLE001
        st.error(
            "Chatbot is not configured. Add GROQ_API_KEY and MCP_AUTH_TOKEN to "
            ".streamlit/secrets.toml (see .streamlit/secrets.toml.example).\n\n"
            f"Details: {e}"
        )
        st.stop()


def _init_state() -> None:
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = str(uuid.uuid4())
    if "messages" not in st.session_state:
        st.session_state.messages = []


def _clear_chat() -> None:
    """Reset the conversation and start a fresh agent-memory thread."""
    st.session_state.messages = []
    st.session_state.thread_id = str(uuid.uuid4())


def _render_message(msg: dict) -> None:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("tool_calls"):
            with st.expander("Tools used"):
                for c in msg["tool_calls"]:
                    st.code(f"{c['name']}({c['args']})", language="python")


def _submit(agent, prompt: str) -> None:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.spinner("Thinking..."):
        try:
            result = answer(agent, st.session_state.thread_id, prompt)
            st.session_state.messages.append(
                {"role": "assistant", "content": result["text"],
                 "tool_calls": result["tool_calls"]}
            )
        except Exception as e:  # noqa: BLE001
            st.session_state.messages.append(
                {"role": "assistant",
                 "content": f"Sorry, something went wrong: {e}", "tool_calls": []}
            )


def render_chat_page() -> None:
    """Full-page chat used by pages/Ask_AI.py, with Clear right beside the input."""
    _init_state()
    agent = ensure_agent()
    for m in st.session_state.messages:
        _render_message(m)

    col_in, col_clear = st.columns([8, 1])
    with col_in:
        prompt = st.chat_input("e.g. Which city has the worst AQI?", key="page_chat_input")
    with col_clear:
        if st.button("Clear", key="page_clear", use_container_width=True):
            _clear_chat()
            st.rerun()

    if prompt:
        _submit(agent, prompt)
        st.rerun()


def render_tools_rules_panel() -> None:
    """List the live MCP tools the assistant can call and its operating rules."""
    st.markdown(f"**MCP server:** [live on Hugging Face]({HF_SPACE_URL})")
    st.markdown("**Tools the assistant can use** (served by the MCP server):")
    for t in tools_info():
        desc = t["description"].splitlines()[0] if t["description"] else ""
        st.markdown(f"- `{t['name']}` - {desc}")
    st.markdown("**Operating rules**")
    st.markdown(
        "- Data is historical (2015-2020) for 11 Indian cities - not real-time.\n"
        "- Answers come only from the tools above; it never invents numbers.\n"
        "- It always reports the as-of date of the data it used.\n"
        "- For now it answers air-quality data questions only."
    )
