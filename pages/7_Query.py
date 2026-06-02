import pandas as pd
import streamlit as st
from modules import calculator
from modules.loader import apply_filters
from modules.auth import require_login
from modules.ui import apply_theme, page_header, section_label, top_filters

require_login()
apply_theme()

if "df" not in st.session_state:
    st.warning("No data loaded. Go to the **Upload** page first.")
    st.stop()

df_raw: pd.DataFrame = st.session_state["df"]
all_months = sorted(df_raw["redemption_month"].dropna().unique().astype(str).tolist())

if not all_months:
    st.warning("No redemption months found in data.")
    st.stop()

page_header("Quick Query", "Instant breakage lookup for any currency and date range")

# Currency + company from the shared filter bar; months are separate dropdowns below
filters   = top_filters(df_raw, key_prefix="query", show_months=False)
currency  = filters["currency"]
companies = filters["companies"]

st.markdown("")
section_label("Date Range")

m_col1, m_col2 = st.columns(2)
with m_col1:
    start_month = st.selectbox("From month", all_months, index=0, key="q_start")
with m_col2:
    end_month = st.selectbox("To month", all_months, index=len(all_months) - 1, key="q_end")

st.markdown("")

if start_month > end_month:
    st.error("'From month' must be on or before 'To month'.")
    st.stop()

df = apply_filters(df_raw, {
    "date_range": (start_month, end_month),
    "countries": None,
    "companies": companies or None,
    "currencies": [currency] if currency else None,
})

if df.empty:
    st.info("No data for that selection. Try a different currency or date range.")
    st.stop()

k  = calculator.kpis(df)
br = round(100 - k["activation_rate"], 2)
period_label = start_month if start_month == end_month else f"{start_month} → {end_month}"

# ── Answer card ───────────────────────────────────────────────────────────────
st.markdown(
    f'<div style="background:linear-gradient(135deg,var(--brand-25),var(--neutral-50));'
    f'border-radius:var(--radius-xl);padding:20px 28px;margin-bottom:20px;'
    f'border:1px solid var(--neutral-200);box-shadow:var(--shadow-sm)">'
    f'<div style="font-size:0.6875rem;font-weight:700;text-transform:uppercase;'
    f'letter-spacing:0.05em;color:var(--accent);margin-bottom:6px">Query Result</div>'
    f'<div style="font-size:0.875rem;color:var(--text-secondary)">'
    f'<strong>{currency}</strong> &nbsp;·&nbsp; {period_label} &nbsp;·&nbsp; '
    f'{k["total"]:,} total records'
    f'{"  ·  " + ", ".join(companies) if companies else ""}'
    f'</div></div>',
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns(4)
c1.metric(
    "Breakage Amount",
    calculator.fmt_amount(k["breakage_amount"], currency),
    help="Total monetary value of cards that were never activated in the selected period.",
)
c2.metric(
    "Breakage Rate",
    f"{br}%",
    help="Breakage Amount ÷ Total Redeemed Amount × 100 for the selected period and currency.",
)
c3.metric(
    "Cards Not Activated",
    f"{k['breakage_count']:,}",
    help="Number of individual gift cards that were redeemed but never activated by the employee.",
)
c4.metric(
    "Total Redeemed",
    calculator.fmt_amount(k["total_amount"], currency),
    help="Total value of all gift cards issued in the selected period — both activated and not activated.",
)

st.markdown("")

# ── Month-by-month breakdown ──────────────────────────────────────────────────
section_label("Month-by-Month Breakdown")
trend = calculator.monthly_trend_v2(df)
if not trend.empty:
    disp = trend.copy()
    disp["Breakage Rate"]   = (100 - disp["activation_rate"]).round(2).map(lambda v: f"{v}%")
    disp["Activation Rate"] = disp["activation_rate"].map(lambda v: f"{v}%")
    disp["Breakage Amount"] = disp["breakage_amount"].map(
        lambda v: calculator.fmt_amount(v, currency)
    )
    disp = disp.rename(columns={
        "redemption_month": "Month", "total": "Total",
        "activated": "Activated", "breakage_count": "Not Activated",
    })[["Month", "Total", "Activated", "Activation Rate", "Not Activated",
        "Breakage Amount", "Breakage Rate"]]
    st.dataframe(disp, use_container_width=True, hide_index=True)

st.markdown("")

# ── Top companies ─────────────────────────────────────────────────────────────
section_label("Top Companies by Breakage")
company_df = calculator.breakage_by_company(df)
if not company_df.empty:
    top = company_df.head(10).copy()
    top["breakage_amount"] = top["breakage_amount"].map(
        lambda v: calculator.fmt_amount(v, currency)
    )
    top["breakage_rate"]   = top["breakage_rate"].map(lambda v: f"{v}%")
    top = top.rename(columns={
        "company": "Company", "total_count": "Total Cards",
        "breakage_count": "Not Activated", "breakage_amount": "Breakage Amount",
        "breakage_rate": "Breakage Rate",
    })[["Company", "Total Cards", "Not Activated", "Breakage Amount", "Breakage Rate"]]
    st.dataframe(top, use_container_width=True, hide_index=True)
