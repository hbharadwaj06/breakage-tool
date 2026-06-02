import hashlib
import json
import os
import streamlit as st

_USERS_FILE = os.path.join(os.path.dirname(__file__), "..", "config", "users.json")


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _load_users() -> dict:
    try:
        if "users" in st.secrets:
            return {k: dict(v) for k, v in st.secrets["users"].items()}
    except Exception:
        pass
    if not os.path.exists(_USERS_FILE):
        return {}
    with open(_USERS_FILE) as f:
        return json.load(f)


def _login_screen():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Hide sidebar and all chrome */
    [data-testid="stSidebar"],
    [data-testid="stSidebarNav"],
    [data-testid="stToolbar"],
    header { display: none !important; }

    /* Full-page background */
    .stApp {
        background: linear-gradient(135deg, #1a0f2e 0%, #2d1b4e 50%, #1a0f2e 100%) !important;
        font-family: 'Inter', system-ui, sans-serif !important;
    }

    /* Remove default padding */
    .main .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }

    /* Card */
    .login-card {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 20px;
        padding: 48px 44px 40px;
        backdrop-filter: blur(20px);
        box-shadow: 0 32px 64px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.05);
    }

    /* Logo mark */
    .login-logo {
        width: 52px; height: 52px;
        background: linear-gradient(135deg, #ff6d05, #e06000);
        border-radius: 14px;
        display: flex; align-items: center; justify-content: center;
        margin: 0 auto 24px;
        box-shadow: 0 8px 24px rgba(255,109,5,0.35);
    }

    /* Headings */
    .login-title {
        font-size: 1.6rem; font-weight: 700;
        color: #ffffff; text-align: center;
        margin: 0 0 6px; letter-spacing: -0.02em;
    }
    .login-sub {
        font-size: 0.85rem; color: rgba(255,255,255,0.45);
        text-align: center; margin: 0 0 36px;
        letter-spacing: 0.01em;
    }

    /* Input labels */
    .login-label {
        font-size: 0.78rem; font-weight: 600;
        color: rgba(255,255,255,0.6);
        text-transform: uppercase; letter-spacing: 0.07em;
        margin-bottom: 6px;
    }

    /* Override Streamlit inputs */
    [data-testid="stTextInput"] input {
        background: rgba(255,255,255,0.07) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        border-radius: 10px !important;
        color: #ffffff !important;
        font-size: 0.95rem !important;
        padding: 12px 14px !important;
        caret-color: #ff6d05;
        transition: border-color 200ms, box-shadow 200ms;
    }
    [data-testid="stTextInput"] input:focus {
        border-color: #ff6d05 !important;
        box-shadow: 0 0 0 3px rgba(255,109,5,0.20) !important;
        outline: none !important;
    }
    [data-testid="stTextInput"] input::placeholder { color: rgba(255,255,255,0.25) !important; }
    [data-testid="stTextInput"] label { color: rgba(255,255,255,0.55) !important; font-size: 0.78rem !important; font-weight: 600 !important; text-transform: uppercase; letter-spacing: 0.07em; }

    /* Submit button */
    [data-testid="stFormSubmitButton"] button {
        background: linear-gradient(135deg, #ff6d05, #e06000) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        padding: 13px !important;
        width: 100% !important;
        margin-top: 8px !important;
        box-shadow: 0 4px 16px rgba(255,109,5,0.35) !important;
        transition: opacity 150ms, transform 150ms !important;
        cursor: pointer !important;
    }
    [data-testid="stFormSubmitButton"] button:hover {
        opacity: 0.92 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(255,109,5,0.45) !important;
    }
    [data-testid="stFormSubmitButton"] button:active { transform: translateY(0) !important; }

    /* Error alert */
    [data-testid="stAlert"] {
        background: rgba(220,53,69,0.12) !important;
        border: 1px solid rgba(220,53,69,0.3) !important;
        border-radius: 10px !important;
        color: #ff8080 !important;
    }

    /* Divider */
    .login-divider {
        border: none;
        border-top: 1px solid rgba(255,255,255,0.08);
        margin: 28px 0;
    }

    /* Footer */
    .login-footer {
        font-size: 0.75rem; color: rgba(255,255,255,0.2);
        text-align: center; margin-top: 28px;
    }

    /* Decorative orbs */
    .orb {
        position: fixed; border-radius: 50%;
        filter: blur(80px); pointer-events: none; z-index: 0;
    }
    .orb-1 {
        width: 400px; height: 400px;
        background: rgba(91,59,151,0.35);
        top: -100px; left: -100px;
    }
    .orb-2 {
        width: 300px; height: 300px;
        background: rgba(255,109,5,0.15);
        bottom: -60px; right: -60px;
    }
    .orb-3 {
        width: 200px; height: 200px;
        background: rgba(91,59,151,0.2);
        top: 50%; right: 20%;
    }
    </style>

    <!-- Decorative orbs -->
    <div class="orb orb-1"></div>
    <div class="orb orb-2"></div>
    <div class="orb orb-3"></div>
    """, unsafe_allow_html=True)

    # Centre the card
    _, col, _ = st.columns([1, 1.1, 1])
    with col:
        st.markdown("<div style='height:60px'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div class="login-card">
            <div class="login-logo">
                <svg width="26" height="26" viewBox="0 0 24 24" fill="none"
                     stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="3" y="3" width="18" height="18" rx="2"/>
                    <path d="M3 9h18M9 21V9"/>
                    <path d="M15 15l-2-2-2 2"/>
                </svg>
            </div>
            <div class="login-title">Breakage Analysis</div>
            <div class="login-sub">VANTAGE CIRCLE &nbsp;·&nbsp; INTERNAL ANALYTICS</div>
        </div>
        """, unsafe_allow_html=True)

        # Streamlit form rendered on top of the card via negative margin
        st.markdown("<div style='margin-top:-12px; padding: 0 2px'>", unsafe_allow_html=True)
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Sign In →", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("""
        <div class="login-footer">
            Secure access · Internal use only
        </div>
        """, unsafe_allow_html=True)

    if submitted:
        users = _load_users()
        u = users.get(username)
        if u and u.get("password_hash") == _hash(password):
            st.session_state["_auth_user"] = username
            st.session_state["_auth_role"] = u["role"]
            st.session_state["_auth_name"] = u.get("name", username)
            st.rerun()
        else:
            _, col, _ = st.columns([1, 1.1, 1])
            with col:
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
            <div style="display:flex;align-items:center;gap:10px;font-size:1rem;font-weight:700;color:white;letter-spacing:-0.01em">
                <div style="display:flex;align-items:center;justify-content:center;width:32px;height:32px;background:rgba(255,109,5,0.18);border-radius:8px;flex-shrink:0">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#ff6d05" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/><path d="M15 15l-2-2-2 2"/></svg>
                </div>
                Breakage Analysis
            </div>
            <div style="font-size:0.75rem;color:rgba(255,255,255,0.5);margin-top:3px">
                Vantage Circle · Internal
            </div>
        </div>
        """, unsafe_allow_html=True)

        # spacer — navigation auto-renders here by Streamlit

        st.markdown("""<div style="margin-top:auto"></div>""", unsafe_allow_html=True)
        st.markdown("---")
        role_badge = "Admin" if is_admin() else "Viewer"
        role_color = "var(--accent)" if is_admin() else "rgba(255,255,255,0.5)"
        st.markdown(
            f'<div style="padding:0 4px 8px">'
            f'<div style="font-size:0.875rem;color:rgba(255,255,255,0.75);font-weight:500">{current_user()}</div>'
            f'<div style="font-size:0.75rem;color:{role_color};margin-top:2px">● {role_badge}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if st.button("Sign Out", use_container_width=True, key="_signout"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()
