import streamlit as st
from modules.auth import require_login, is_admin, sidebar_user_widget
from modules.ui import apply_theme

st.set_page_config(
    page_title="Breakage Analysis — Vantage Circle",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_theme()
require_login()
sidebar_user_widget()

# Register navigation FIRST so Streamlit never falls back to auto-discovery
pages = [
    st.Page("pages/2_Overview.py", title="Overview", icon="📊"),
    st.Page("pages/8_Global.py",   title="Global View", icon="🌐"),
    st.Page("pages/7_Query.py",    title="Quick Query", icon="🔍"),
    st.Page("pages/3_Breakage.py", title="Breakage", icon="🔴"),
    st.Page("pages/4_Behavior.py", title="Behavior", icon="📈"),
    st.Page("pages/5_Insights.py", title="Insights", icon="💡"),
    st.Page("pages/6_Export.py",   title="Export", icon="📥"),
]

if is_admin():
    pages.append(st.Page("pages/1_Upload.py", title="Upload Data", icon="📤"))

pg = st.navigation(pages)

# Load data after navigation is registered (so spinner shows inside correct nav context)
if "df" not in st.session_state:
    from modules.loader import get_stored_files, load_from_store
    if get_stored_files():
        try:
            with st.spinner("Loading data…"):
                _df, _warnings = load_from_store()
            for w in _warnings:
                st.warning(w)
            if _df is not None:
                st.session_state["df"] = _df
            else:
                st.error("Data store returned empty — open Upload page to rebuild.")
        except Exception as _e:
            import traceback
            st.error(f"Failed to load data: {_e}")
            st.code(traceback.format_exc())

pg.run()
