import pathlib
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Lao PDR Salary Tax Calculator",
    page_icon="🇱🇦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Hide Streamlit chrome so the embedded app fills the frame cleanly
st.markdown(
    """
    <style>
        #root > div:first-child { padding: 0 !important; }
        header[data-testid="stHeader"] { display: none; }
        .block-container { padding: 0 !important; max-width: 100% !important; }
        footer { display: none; }
        [data-testid="stToolbar"] { display: none; }
    </style>
    """,
    unsafe_allow_html=True,
)

BASE = pathlib.Path(__file__).parent

html = (BASE / "index.html").read_text(encoding="utf-8")
css  = (BASE / "assets" / "tailwind.css").read_text(encoding="utf-8")

# Swap relative CSS link for inline styles so it works inside the Streamlit iframe
html = html.replace(
    '<link rel="stylesheet" href="/assets/tailwind.css">',
    f"<style>\n{css}\n</style>",
)

components.html(html, height=900, scrolling=True)
