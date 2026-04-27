import hashlib
import json
import os
import streamlit as st

_USERS_FILE = os.path.join(os.path.dirname(__file__), "..", "config", "users.json")


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _load_users() -> dict:
    if not os.path.exists(_USERS_FILE):
        return {}
    with open(_USERS_FILE) as f:
        return json.load(f)


def _login_screen():
    st.markdown("""
    <style>
    [data-testid="stSidebarNav"] { display: none; }
    </style>
    """, unsafe_allow_html=True)

    col_l, col_m, col_r = st.columns([1, 1.2, 1])
    with col_m:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("## Breakage Analysis")
        st.markdown("**Vantage Circle** · Internal Analytics Platform")
        st.markdown("---")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign In", use_container_width=True)

        if submitted:
            users = _load_users()
            u = users.get(username)
            if u and u.get("password_hash") == _hash(password):
                st.session_state["_auth_user"] = username
                st.session_state["_auth_role"] = u["role"]
                st.session_state["_auth_name"] = u.get("name", username)
                st.rerun()
            else:
                st.error("Invalid username or password.")


def require_login():
    """Call at the top of every page. Blocks if not authenticated."""
    if "_auth_user" not in st.session_state:
        _login_screen()
        st.stop()


def is_admin() -> bool:
    return st.session_state.get("_auth_role") == "admin"


def current_user() -> str:
    return st.session_state.get("_auth_name", "")


def current_role() -> str:
    return st.session_state.get("_auth_role", "")


def sidebar_user_widget():
    """Render branding, logged-in user badge + sign-out button in sidebar."""
    with st.sidebar:
        st.markdown("""
        <div style="padding:20px 16px 14px;border-bottom:1px solid rgba(255,255,255,0.08);margin-bottom:6px">
            <div style="font-size:1.05em;font-weight:700;color:white;letter-spacing:-0.01em">
                📊 Breakage Analysis
            </div>
            <div style="font-size:0.72em;color:rgba(200,200,232,0.6);margin-top:3px">
                Vantage Circle · Internal
            </div>
        </div>
        """, unsafe_allow_html=True)

        # spacer — navigation auto-renders here by Streamlit

        st.markdown("""<div style="margin-top:auto"></div>""", unsafe_allow_html=True)
        st.markdown("---")
        role_badge = "Admin" if is_admin() else "Viewer"
        role_color = "#ff8c38" if is_admin() else "#c8c8e8"
        st.markdown(
            f'<div style="padding:0 4px 8px">'
            f'<div style="font-size:0.88em;color:#c8c8e8;font-weight:500">{current_user()}</div>'
            f'<div style="font-size:0.72em;color:{role_color};margin-top:2px">● {role_badge}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if st.button("Sign Out", use_container_width=True, key="_signout"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()
