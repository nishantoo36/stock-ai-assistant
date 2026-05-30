import streamlit as st

# Page config must be the first Streamlit call.
st.set_page_config(
    page_title="AI Investment Assistant",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from core.app_shell import render_app


render_app()
