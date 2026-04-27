import streamlit as st

_PRIMARY = ["USD", "INR"]

# ── Vantage Circle Design System CSS ─────────────────────────────────────────
VC_CSS = """
<style>
/* ── Chrome & defaults ── */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
[data-testid="stHeader"] { background: transparent !important; height: 0 !important; }
[data-testid="stToolbar"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }

/* ── Main content background ── */
.main { background: #f4f5fe !important; }
.block-container {
    padding-top: 1.4rem !important;
    padding-bottom: 2.5rem !important;
    max-width: 1280px !important;
}

/* ── Sidebar: VC dark navy ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #29294c 0%, #1e1e3a 100%) !important;
    border-right: none !important;
    box-shadow: 4px 0 20px rgba(0,0,0,0.15) !important;
}
section[data-testid="stSidebar"] > div:first-child {
    background: transparent !important;
}
/* Sidebar text */
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label {
    color: #c8c8e8 !important;
}
/* Sidebar nav links */
[data-testid="stSidebarNav"] a,
[data-testid="stSidebarNav"] span {
    color: #c8c8e8 !important;
    border-radius: 8px !important;
    font-size: 0.9em !important;
    transition: all 0.18s ease !important;
}
[data-testid="stSidebarNav"] a:hover {
    background: rgba(255,109,5,0.18) !important;
    color: #ff8c38 !important;
}
[data-testid="stSidebarNav"] a[aria-current="page"],
[data-testid="stSidebarNav"] li[aria-selected="true"] a {
    background: rgba(255,109,5,0.22) !important;
    color: #ff6d05 !important;
    font-weight: 600 !important;
    border-left: 3px solid #ff6d05 !important;
}
/* Sidebar sign-out button */
section[data-testid="stSidebar"] .stButton > button {
    background: rgba(255,109,5,0.12) !important;
    color: #ff8c38 !important;
    border: 1px solid rgba(255,109,5,0.35) !important;
    border-radius: 8px !important;
    font-size: 0.88em !important;
    font-weight: 500 !important;
    transition: all 0.18s ease !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: #ff6d05 !important;
    color: white !important;
    border-color: #ff6d05 !important;
}

/* ── KPI metric cards ── */
[data-testid="metric-container"] {
    background: white !important;
    border-radius: 14px !important;
    border: 1px solid #ededf5 !important;
    border-top: 4px solid #ff6d05 !important;
    padding: 22px 18px 18px !important;
    box-shadow: 0 2px 16px rgba(41,41,76,0.07) !important;
    transition: box-shadow 0.2s ease !important;
}
[data-testid="metric-container"]:hover {
    box-shadow: 0 4px 24px rgba(41,41,76,0.12) !important;
}
[data-testid="stMetricValue"] {
    font-size: 1.7em !important;
    font-weight: 700 !important;
    color: #29294c !important;
    letter-spacing: -0.02em !important;
}
[data-testid="stMetricLabel"] {
    font-size: 0.7em !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.09em !important;
    color: #9ca3af !important;
}
[data-testid="stMetricDelta"] svg { display: none !important; }
[data-testid="stMetricDelta"] > div {
    font-size: 0.8em !important;
    font-weight: 500 !important;
}

/* ── Filter bar container ── */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: white !important;
    border: 1px solid #ededf5 !important;
    border-radius: 12px !important;
    box-shadow: 0 1px 8px rgba(41,41,76,0.06) !important;
    padding: 4px 8px !important;
}

/* ── Buttons (main area) ── */
.main .stButton > button {
    background: white !important;
    border: 1.5px solid #ededf5 !important;
    border-radius: 8px !important;
    color: #29294c !important;
    font-weight: 500 !important;
    transition: all 0.18s ease !important;
}
.main .stButton > button:hover {
    border-color: #ff6d05 !important;
    color: #ff6d05 !important;
    background: rgba(255,109,5,0.05) !important;
}
.main .stButton > button[kind="primary"] {
    background: #ff6d05 !important;
    color: white !important;
    border: none !important;
    box-shadow: 0 2px 8px rgba(255,109,5,0.35) !important;
}

/* ── Expanders ── */
[data-testid="stExpander"] {
    border: 1px solid #ededf5 !important;
    border-radius: 12px !important;
    background: white !important;
    box-shadow: 0 1px 6px rgba(41,41,76,0.05) !important;
    overflow: hidden;
}
[data-testid="stExpander"] summary {
    font-weight: 600 !important;
    color: #29294c !important;
}

/* ── Data tables ── */
[data-testid="stDataFrame"] {
    border-radius: 12px !important;
    overflow: hidden !important;
    box-shadow: 0 1px 8px rgba(41,41,76,0.07) !important;
    border: 1px solid #ededf5 !important;
}

/* ── Slider ── */
[data-testid="stSlider"] [data-baseweb="slider"] [role="slider"] {
    background: #ff6d05 !important;
    border-color: #ff6d05 !important;
}
[data-baseweb="slider"] [data-testid="stTickBar"] { color: #9ca3af !important; }

/* ── Select/Multiselect ── */
[data-baseweb="select"] > div:first-child {
    border-radius: 8px !important;
    border-color: #ededf5 !important;
}
[data-baseweb="select"] > div:first-child:focus-within {
    border-color: #ff6d05 !important;
    box-shadow: 0 0 0 2px rgba(255,109,5,0.15) !important;
}

/* ── Radio (currency selector) ── */
.stRadio > label { display: none; }
.stRadio [data-baseweb="radio"] { gap: 6px !important; }
.stRadio [data-baseweb="radio"] label {
    background: white;
    border: 1.5px solid #ededf5;
    border-radius: 8px;
    padding: 5px 14px !important;
    font-size: 0.88em !important;
    font-weight: 500 !important;
    color: #29294c !important;
    cursor: pointer;
    transition: all 0.15s ease !important;
}
.stRadio [data-baseweb="radio"] label:hover {
    border-color: #ff6d05 !important;
    color: #ff6d05 !important;
}
[data-baseweb="radio"][data-checked="true"] + label,
.stRadio [aria-checked="true"] + label {
    background: #ff6d05 !important;
    border-color: #ff6d05 !important;
    color: white !important;
}

/* ── Tabs (if used) ── */
[data-baseweb="tab-list"] {
    gap: 4px;
    background: #f4f5fe;
    border-radius: 10px;
    padding: 4px;
}
[data-baseweb="tab"] {
    border-radius: 8px !important;
    font-weight: 500 !important;
}
[aria-selected="true"][data-baseweb="tab"] {
    background: white !important;
    color: #ff6d05 !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08) !important;
}

/* ── Dividers ── */
hr {
    border: none !important;
    border-top: 1px solid #ededf5 !important;
    margin: 20px 0 !important;
}

/* ── Plotly chart containers ── */
[data-testid="stPlotlyChart"] {
    background: white;
    border-radius: 12px;
    box-shadow: 0 1px 8px rgba(41,41,76,0.07);
    border: 1px solid #ededf5;
    padding: 8px;
}

/* ── Alerts & info boxes ── */
[data-testid="stAlert"] {
    border-radius: 10px !important;
}
</style>
"""

# ── VC-branded HTML components ────────────────────────────────────────────────

def apply_theme():
    st.markdown(VC_CSS, unsafe_allow_html=True)


def page_header(title: str, meta: str = ""):
    meta_html = f'<div style="font-size:0.8em;color:#9ca3af;margin-top:3px">{meta}</div>' if meta else ""
    st.markdown(f"""
    <div style="
        background:white; border-radius:14px; padding:18px 24px;
        margin-bottom:18px; display:flex; align-items:center; gap:16px;
        box-shadow:0 2px 12px rgba(41,41,76,0.07); border:1px solid #ededf5;
    ">
        <div style="
            width:5px; min-height:40px; border-radius:3px;
            background:linear-gradient(180deg,#ff6d05 0%,#654ab7 100%);
            flex-shrink:0;
        "></div>
        <div>
            <div style="font-size:1.3em;font-weight:700;color:#29294c;letter-spacing:-0.01em">{title}</div>
            {meta_html}
        </div>
    </div>
    """, unsafe_allow_html=True)


def section_label(text: str):
    st.markdown(
        f'<div style="font-size:0.72em;font-weight:700;letter-spacing:0.1em;'
        f'text-transform:uppercase;color:#654ab7;margin:20px 0 8px">{text}</div>',
        unsafe_allow_html=True,
    )


def insight_card(text: str, variant: str = "default"):
    colors = {
        "default": "#ff6d05",
        "alert":   "#f15162",
        "neutral": "#654ab7",
        "warn":    "#ff9e33",
    }
    color = colors.get(variant, "#ff6d05")
    st.markdown(f"""
    <div style="
        background:white; border-left:4px solid {color}; border-radius:8px;
        padding:14px 18px; margin-bottom:10px; font-size:0.95em; line-height:1.65;
        color:#1f2937; box-shadow:0 1px 6px rgba(41,41,76,0.06);
    ">{text}</div>
    """, unsafe_allow_html=True)


def summary_card(text: str):
    st.markdown(f"""
    <div style="
        background:linear-gradient(135deg,#fef3ed 0%,#f4f5fe 100%);
        border-left:4px solid #ff6d05; border-radius:12px;
        padding:20px 26px; margin-bottom:20px; font-size:1em; line-height:1.8;
        color:#29294c; box-shadow:0 2px 10px rgba(41,41,76,0.07);
    ">{text}</div>
    """, unsafe_allow_html=True)


# ── Currency selector ─────────────────────────────────────────────────────────

def currency_selector(df_raw, key_prefix: str = "main") -> str:
    available = sorted(df_raw["Currency"].dropna().unique().tolist())
    if not available:
        return None
    if len(available) == 1:
        st.markdown(f"`{available[0]}`")
        return available[0]

    primary = [c for c in _PRIMARY if c in available]
    others  = [c for c in available if c not in _PRIMARY]
    radio_opts = primary + (["Other…"] if others else [])
    default_idx = radio_opts.index("USD") if "USD" in radio_opts else 0

    selected = st.radio(
        "Currency",
        radio_opts,
        index=default_idx,
        horizontal=True,
        key=f"_cr_{key_prefix}",
    )
    if selected == "Other…":
        return st.selectbox("Select currency", others, key=f"_co_{key_prefix}",
                            label_visibility="collapsed")
    return selected


# ── Top filter bar ────────────────────────────────────────────────────────────

def top_filters(
    df_raw,
    key_prefix: str = "main",
    show_currency: bool = True,
    show_months: bool = True,
    show_companies: bool = True,
) -> dict:
    """
    Renders a horizontal filter strip. Returns dict with keys:
    currency, date_range (tuple of str), companies (list).
    """
    all_months = sorted(df_raw["redemption_month"].dropna().unique().astype(str).tolist())

    # Count visible columns: currency gets 1.2, months get 2, companies get 2
    weights = []
    if show_currency: weights.append(1.3)
    if show_months:   weights.append(2.2)
    if show_companies: weights.append(2.0)

    results: dict = {}

    with st.container(border=True):
        cols = st.columns(weights) if weights else []
        col_idx = 0

        if show_currency:
            with cols[col_idx]:
                st.markdown(
                    '<p style="font-size:0.7em;font-weight:700;text-transform:uppercase;'
                    'letter-spacing:0.09em;color:#ff6d05;margin-bottom:2px">Currency</p>',
                    unsafe_allow_html=True,
                )
                results["currency"] = currency_selector(df_raw, key_prefix=key_prefix)
            col_idx += 1

        if show_months and all_months:
            with cols[col_idx]:
                st.markdown(
                    '<p style="font-size:0.7em;font-weight:700;text-transform:uppercase;'
                    'letter-spacing:0.09em;color:#ff6d05;margin-bottom:2px">Period</p>',
                    unsafe_allow_html=True,
                )
                results["date_range"] = st.select_slider(
                    "Period",
                    options=all_months,
                    value=(all_months[0], all_months[-1]),
                    key=f"_dr_{key_prefix}",
                    label_visibility="collapsed",
                )
            col_idx += 1
        else:
            results["date_range"] = (all_months[0], all_months[-1]) if all_months else None

        if show_companies:
            with cols[col_idx]:
                st.markdown(
                    '<p style="font-size:0.7em;font-weight:700;text-transform:uppercase;'
                    'letter-spacing:0.09em;color:#ff6d05;margin-bottom:2px">Company</p>',
                    unsafe_allow_html=True,
                )
                results["companies"] = st.multiselect(
                    "Company",
                    sorted(df_raw["Company"].dropna().unique()),
                    default=[],
                    key=f"_cm_{key_prefix}",
                    label_visibility="collapsed",
                    placeholder="All companies",
                )
        else:
            results["companies"] = []

    return results
