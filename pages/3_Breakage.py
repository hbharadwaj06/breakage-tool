import pandas as pd
import streamlit as st
from modules import calculator, charts
from modules.loader import apply_filters
from modules.auth import require_login
from modules.ui import apply_theme, page_header, section_label, top_filters

require_login()
apply_theme()

if "df" not in st.session_state:
    st.warning("No data loaded. Go to the **Upload** page first.")
    st.stop()

df_raw: pd.DataFrame = st.session_state["df"]

page_header("Breakage Deep-Dive", "By client · denomination · card type · brand · geography")

filters   = top_filters(df_raw, key_prefix="breakage")
currency  = filters["currency"]
date_range = filters["date_range"]
companies = filters["companies"]

df = apply_filters(df_raw, {
    "date_range": date_range,
    "countries": None,
    "companies": companies or None,
    "currencies": [currency] if currency else None,
})

if df.empty:
    st.warning("No data matches the current filters.")
    st.stop()

st.markdown("")

# ── By Client ─────────────────────────────────────────────────────────────────
section_label("Breakage by Client")
company_df = calculator.breakage_by_company(df)

if not company_df.empty:
    avg_rate = company_df["breakage_rate"].mean()
    col_l, col_r = st.columns([2, 1])
    with col_l:
        st.plotly_chart(charts.company_breakage_chart(company_df), use_container_width=True)
    with col_r:
        display = company_df.head(15).copy()
        flag = display["breakage_rate"].apply(lambda v: "⚠️" if v > avg_rate * 1.3 else "")
        display["breakage_rate"] = display["breakage_rate"].map(lambda v: f"{v}%")
        display[""] = flag
        st.dataframe(
            display[["company", "total_count", "breakage_count", "breakage_rate", ""]].rename(
                columns={"company": "Company", "total_count": "Total",
                         "breakage_count": "Breakage", "breakage_rate": "Rate"}
            ),
            use_container_width=True, hide_index=True,
        )
    st.caption(f"Average breakage rate across clients: {avg_rate:.1f}%  ·  ⚠️ = more than 30% above average")

st.markdown("")

# ── By Denomination ───────────────────────────────────────────────────────────
section_label("Breakage by Denomination")
denom = calculator.breakage_by_denomination(df, currency=currency)

c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(charts.denomination_bar(denom), use_container_width=True)
with c2:
    st.plotly_chart(charts.denomination_count_bar(denom), use_container_width=True)

st.dataframe(denom, use_container_width=True, hide_index=True)

st.markdown("")

# ── Open Loop vs Closed Loop ──────────────────────────────────────────────────
section_label("Open Loop vs Closed Loop")
card_type = calculator.breakage_by_card_type(df)

c1, c2 = st.columns([1, 2])
with c1:
    st.plotly_chart(charts.card_type_donut(card_type), use_container_width=True)
with c2:
    st.dataframe(card_type, use_container_width=True, hide_index=True)

st.markdown("")

# ── By Brand ──────────────────────────────────────────────────────────────────
section_label("Breakage by Brand")
top_n = st.slider("Show top N brands", min_value=5, max_value=50, value=15, key="brand_n")
brand = calculator.breakage_by_brand(df)
st.plotly_chart(charts.brand_bar(brand, top_n=top_n), use_container_width=True)
st.dataframe(brand.head(top_n), use_container_width=True, hide_index=True)

st.markdown("")

# ── By Country ────────────────────────────────────────────────────────────────
section_label("Breakage by Country")
geo = calculator.breakage_by_geography(df)
c1, c2 = st.columns([2, 1])
with c1:
    st.plotly_chart(charts.geography_treemap(geo), use_container_width=True)
with c2:
    st.dataframe(geo, use_container_width=True, hide_index=True)
