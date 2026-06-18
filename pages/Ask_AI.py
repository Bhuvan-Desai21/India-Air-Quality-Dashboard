# pages/Ask_AI.py
"""Ask AI - full-page chat with the air-quality agent, plus a how-it-works panel."""

import streamlit as st

st.set_page_config(page_title="Ask AI - Air Quality", page_icon=None, layout="wide")

from utils.style import apply_brand_style  # noqa: E402
from chatbot.ui import ensure_agent, render_chat_page, render_tools_rules_panel  # noqa: E402

apply_brand_style()

st.title("Ask AI")
st.caption("Ask about AQI and pollutants across 11 Indian cities (2015-2020, historical).")

ensure_agent()  # build the shared agent up front so the panel can list the live tools

with st.expander("What this assistant can do", expanded=True):
    render_tools_rules_panel()

render_chat_page()
