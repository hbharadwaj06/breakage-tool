import streamlit as st

_PRIMARY = ["USD", "INR"]

# ── Vantage Circle Design System CSS ─────────────────────────────────────────
VC_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ── Design system tokens ── */
:root {
  --brand-25:  #f6f4fb;
  --brand-50:  #f1edf8;
  --brand-100: #e2daf1;
  --brand-200: #c5b5e2;
  --brand-300: #a086d0;
  --brand-400: #7a56bd;
  --brand-500: #5b3b97;
  --brand-600: #472e75;

  --neutral-50:  #f5f5f7;
  --neutral-100: #eff2f5;
  --neutral-200: #eef0f4;
  --neutral-300: #d9dde7;
  --neutral-400: #637281;
  --neutral-500: #5c6c7c;
  --neutral-600: #475467;

  --text-primary:   #33475b;
  --text-secondary: #5c6c7c;
  --color-white:    #ffffff;

  --color-success:  #28a745;
  --color-error:    #dc3545;
  --color-warning:  #ffc107;

  --color-focus: rgba(91, 59, 151, 0.25);

  --accent:       #ff6d05;
  --accent-hover: #e06000;

  --radius:      8px;
  --radius-md:   10px;
  --radius-lg:   12px;
  --radius-xl:   16px;
  --radius-pill: 50px;

  --shadow-xs: 0px 1px 2px rgba(16, 24, 40, 0.05);
  --shadow-sm: 0px 1px 3px rgba(16, 24, 40, 0.10), 0px 1px 2px rgba(16, 24, 40, 0.06);
  --shadow-md: 0px 4px 8px rgba(16, 24, 40, 0.10), 0px 2px 4px rgba(16, 24, 40, 0.06);
  --shadow-lg: 0px 12px 16px rgba(16, 24, 40, 0.08), 0px 4px 6px rgba(16, 24, 40, 0.03);

  --duration-fast: 150ms;
  --duration-base: 200ms;
  --duration-slow: 300ms;
  --ease-in-out:   cubic-bezier(0.65, 0, 0.35, 1);
  --ease-out:      cubic-bezier(0.16, 1, 0.3, 1);
}

/* ── Global base ── */
html, body, [class*="css"] {
    font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
}
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
[data-testid="stHeader"]     { background: transparent !important; height: 0 !important; }
[data-testid="stToolbar"]    { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }

/* ── Page background ── */
.main { background: var(--neutral-50) !important; }
.block-container {
    padding-top:    1.4rem !important;
    padding-bottom: 2.5rem !important;
    max-width: 1280px !important;
}

/* ── Sidebar — VC midnight navy ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #29294c 0%, #1e1e3a 100%) !important;
    border-right: none !important;
    box-shadow: 4px 0 20px rgba(0, 0, 0, 0.18) !important;
}
section[data-testid="stSidebar"] > div:first-child {
    background: transparent !important;
}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label {
    color: rgba(255, 255, 255, 0.7) !important;
}

/* Sidebar nav links */
[data-testid="stSidebarNav"] a,
[data-testid="stSidebarNav"] span {
    color: rgba(255, 255, 255, 0.65) !important;
    border-radius: var(--radius-lg) !important;
    font-size: 0.875rem !important;
    font-weight: 500 !important;
    transition: background-color var(--duration-base) var(--ease-in-out),
                color var(--duration-base) var(--ease-in-out) !important;
}
[data-testid="stSidebarNav"] a:hover {
    background: rgba(255, 255, 255, 0.08) !important;
    color: #ffffff !important;
}
[data-testid="stSidebarNav"] a[aria-current="page"],
[data-testid="stSidebarNav"] li[aria-selected="true"] a {
    background: rgba(255, 109, 5, 0.18) !important;
    color: var(--accent) !important;
    font-weight: 600 !important;
    border-left: 3px solid var(--accent) !important;
}

/* Sidebar sign-out button */
section[data-testid="stSidebar"] .stButton > button {
    background: rgba(255, 255, 255, 0.06) !important;
    color: rgba(255, 255, 255, 0.65) !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    border-radius: var(--radius-pill) !important;
    font-size: 0.8125rem !important;
    font-weight: 500 !important;
    transition: background-color var(--duration-base) var(--ease-in-out),
                border-color var(--duration-base) var(--ease-in-out),
                color var(--duration-base) var(--ease-in-out) !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: var(--accent) !important;
    color: #ffffff !important;
    border-color: var(--accent) !important;
}

/* ── KPI metric cards ── */
[data-testid="metric-container"] {
    background: var(--color-white) !important;
    border-radius: var(--radius-xl) !important;
    border: 1px solid var(--neutral-200) !important;
    border-left: 4px solid var(--brand-500) !important;
    padding: 20px 18px 18px !important;
    box-shadow: var(--shadow-sm) !important;
    transition: box-shadow var(--duration-slow) var(--ease-out),
                transform var(--duration-slow) var(--ease-out) !important;
}
[data-testid="metric-container"]:hover {
    box-shadow: var(--shadow-md) !important;
    transform: translateY(-2px) !important;
}
[data-testid="stMetricValue"] {
    font-size: 1.5rem !important;
    font-weight: 700 !important;
    color: var(--text-primary) !important;
    letter-spacing: -0.02em !important;
    line-height: 1.2 !important;
}
[data-testid="stMetricLabel"] {
    font-size: 0.6875rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    color: var(--neutral-400) !important;
}
[data-testid="stMetricDelta"] svg { display: none !important; }
[data-testid="stMetricDelta"] > div {
    font-size: 0.8125rem !important;
    font-weight: 500 !important;
}

/* ── Filter / container borders ── */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--color-white) !important;
    border: 1px solid var(--neutral-200) !important;
    border-radius: var(--radius-lg) !important;
    box-shadow: var(--shadow-xs) !important;
    padding: 4px 8px !important;
}

/* ── Buttons (main area) ── */
.main .stButton > button {
    background: var(--color-white) !important;
    border: 1.5px solid var(--neutral-300) !important;
    border-radius: var(--radius-pill) !important;
    color: var(--text-primary) !important;
    font-weight: 500 !important;
    font-size: 0.8125rem !important;
    transition: background-color var(--duration-base) var(--ease-in-out),
                border-color var(--duration-base) var(--ease-in-out),
                color var(--duration-base) var(--ease-in-out),
                box-shadow var(--duration-slow) var(--ease-out),
                transform var(--duration-slow) var(--ease-out) !important;
}
.main .stButton > button:hover {
    border-color: var(--brand-500) !important;
    color: var(--brand-500) !important;
    background: var(--brand-25) !important;
    box-shadow: var(--shadow-md) !important;
    transform: translateY(-1px) !important;
}
.main .stButton > button:focus-visible {
    box-shadow: 0 0 0 4px var(--color-focus) !important;
    outline: none !important;
}
.main .stButton > button[kind="primary"] {
    background: var(--brand-500) !important;
    color: var(--color-white) !important;
    border: none !important;
    box-shadow: 0 2px 8px rgba(91, 59, 151, 0.35) !important;
}
.main .stButton > button[kind="primary"]:hover {
    background: var(--brand-600) !important;
    color: var(--color-white) !important;
}

/* ── Expanders ── */
[data-testid="stExpander"] {
    border: 1px solid var(--neutral-200) !important;
    border-radius: var(--radius-lg) !important;
    background: var(--color-white) !important;
    box-shadow: var(--shadow-xs) !important;
    overflow: hidden !important;
}
[data-testid="stExpander"] summary {
    font-weight: 600 !important;
    color: var(--text-primary) !important;
    font-size: 0.875rem !important;
}

/* ── Data tables ── */
[data-testid="stDataFrame"] {
    border-radius: var(--radius-lg) !important;
    overflow: hidden !important;
    box-shadow: var(--shadow-sm) !important;
    border: 1px solid var(--neutral-200) !important;
}

/* ── Slider ── */
[data-testid="stSlider"] [data-baseweb="slider"] [role="slider"] {
    background: var(--brand-500) !important;
    border-color: var(--brand-500) !important;
}
[data-baseweb="slider"] [data-testid="stTickBar"] {
    color: var(--neutral-400) !important;
}

/* ── Select / Multiselect ── */
[data-baseweb="select"] > div:first-child {
    border-radius: var(--radius) !important;
    border-color: var(--neutral-300) !important;
    background: var(--color-white) !important;
}
[data-baseweb="select"] > div:first-child:focus-within {
    border-color: var(--brand-500) !important;
    box-shadow: 0 0 0 3px var(--color-focus) !important;
}

/* ── Radio (currency selector) ── */
.stRadio > label { display: none !important; }
.stRadio [data-baseweb="radio"] { gap: 6px !important; }
.stRadio [data-baseweb="radio"] label {
    background: var(--color-white) !important;
    border: 1.5px solid var(--neutral-300) !important;
    border-radius: var(--radius-pill) !important;
    padding: 5px 14px !important;
    font-size: 0.8125rem !important;
    font-weight: 500 !important;
    color: var(--text-primary) !important;
    cursor: pointer !important;
    transition: background-color var(--duration-fast) var(--ease-in-out),
                border-color var(--duration-fast) var(--ease-in-out),
                color var(--duration-fast) var(--ease-in-out) !important;
}
.stRadio [data-baseweb="radio"] label:hover {
    border-color: var(--brand-500) !important;
    color: var(--brand-500) !important;
    background: var(--brand-25) !important;
}
[data-baseweb="radio"][data-checked="true"] + label,
.stRadio [aria-checked="true"] + label {
    background: var(--brand-500) !important;
    border-color: var(--brand-500) !important;
    color: var(--color-white) !important;
}

/* ── Tabs ── */
[data-baseweb="tab-list"] {
    gap: 4px !important;
    background: var(--neutral-100) !important;
    border-radius: var(--radius-md) !important;
    padding: 4px !important;
}
[data-baseweb="tab"] {
    border-radius: var(--radius) !important;
    font-weight: 500 !important;
    font-size: 0.875rem !important;
    color: var(--text-secondary) !important;
    transition: background-color var(--duration-base) var(--ease-in-out),
                color var(--duration-base) var(--ease-in-out) !important;
}
[aria-selected="true"][data-baseweb="tab"] {
    background: var(--color-white) !important;
    color: var(--brand-500) !important;
    box-shadow: var(--shadow-xs) !important;
}

/* ── Dividers ── */
hr {
    border: none !important;
    border-top: 1px solid var(--neutral-200) !important;
    margin: 20px 0 !important;
}

/* ── Plotly chart containers ── */
[data-testid="stPlotlyChart"] {
    background: var(--color-white) !important;
    border-radius: var(--radius-lg) !important;
    box-shadow: var(--shadow-sm) !important;
    border: 1px solid var(--neutral-200) !important;
    padding: 8px !important;
}

/* ── Alerts ── */
[data-testid="stAlert"] {
    border-radius: var(--radius-lg) !important;
    font-size: 0.875rem !important;
}
</style>
"""

# ── VC-branded HTML components ────────────────────────────────────────────────

def apply_theme():
    st.markdown(VC_CSS, unsafe_allow_html=True)


def page_header(title: str, meta: str = ""):
    meta_html = (
        f'<div style="font-size:0.75rem;color:var(--neutral-400);margin-top:3px;'
        f'font-weight:400">{meta}</div>'
        if meta else ""
    )
    st.markdown(f"""
    <div style="
        background:var(--color-white); border-radius:var(--radius-xl);
        padding:18px 24px; margin-bottom:18px;
        display:flex; align-items:center; gap:16px;
        box-shadow:var(--shadow-sm); border:1px solid var(--neutral-200);
    ">
        <div style="
            width:4px; min-height:40px; border-radius:2px;
            background:linear-gradient(180deg, var(--brand-500) 0%, var(--accent) 100%);
            flex-shrink:0;
        "></div>
        <div>
            <div style="
                font-size:1.125rem; font-weight:700;
                color:var(--text-primary); letter-spacing:-0.01em;
                line-height:1.2; font-family:inherit;
            ">{title}</div>
            {meta_html}
        </div>
    </div>
    """, unsafe_allow_html=True)


def section_label(text: str):
    st.markdown(
        f'<div style="'
        f'font-size:0.6875rem; font-weight:700; letter-spacing:0.05em;'
        f'text-transform:uppercase; color:var(--brand-500);'
        f'margin:20px 0 8px; font-family:inherit;'
        f'">{text}</div>',
        unsafe_allow_html=True,
    )


def insight_card(text: str, variant: str = "default"):
    colors = {
        "default": "var(--brand-500)",
        "alert":   "var(--color-error)",
        "neutral": "var(--neutral-500)",
        "warn":    "var(--color-warning)",
    }
    border = colors.get(variant, "var(--brand-500)")
    st.markdown(f"""
    <div style="
        background:var(--color-white); border-left:4px solid {border};
        border-radius:var(--radius-lg); padding:14px 18px; margin-bottom:10px;
        font-size:0.875rem; line-height:1.65; color:var(--text-primary);
        box-shadow:var(--shadow-xs); border-top:1px solid var(--neutral-200);
        border-right:1px solid var(--neutral-200); border-bottom:1px solid var(--neutral-200);
        font-family:inherit;
    ">{text}</div>
    """, unsafe_allow_html=True)


def summary_card(text: str):
    st.markdown(f"""
    <div style="
        background:linear-gradient(135deg, var(--brand-25) 0%, var(--neutral-50) 100%);
        border-left:4px solid var(--brand-500);
        border-radius:var(--radius-xl); padding:20px 26px; margin-bottom:20px;
        font-size:0.875rem; line-height:1.8; color:var(--text-primary);
        box-shadow:var(--shadow-sm); font-family:inherit;
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

    weights = []
    if show_currency:  weights.append(1.3)
    if show_months:    weights.append(2.2)
    if show_companies: weights.append(2.0)

    results: dict = {}

    with st.container(border=True):
        cols = st.columns(weights) if weights else []
        col_idx = 0

        if show_currency:
            with cols[col_idx]:
                st.markdown(
                    '<p style="font-size:0.6875rem;font-weight:700;text-transform:uppercase;'
                    'letter-spacing:0.05em;color:var(--accent);margin-bottom:2px;'
                    'font-family:inherit">Currency</p>',
                    unsafe_allow_html=True,
                )
                results["currency"] = currency_selector(df_raw, key_prefix=key_prefix)
            col_idx += 1

        if show_months and all_months:
            with cols[col_idx]:
                st.markdown(
                    '<p style="font-size:0.6875rem;font-weight:700;text-transform:uppercase;'
                    'letter-spacing:0.05em;color:var(--accent);margin-bottom:2px;'
                    'font-family:inherit">Period</p>',
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
                    '<p style="font-size:0.6875rem;font-weight:700;text-transform:uppercase;'
                    'letter-spacing:0.05em;color:var(--accent);margin-bottom:2px;'
                    'font-family:inherit">Company</p>',
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
