import pandas as pd
import plotly.express as px
import streamlit as st
from modules import calculator, charts
from modules.loader import apply_filters
from modules.auth import require_login
from modules.ui import apply_theme, page_header, section_label, insight_card, top_filters

require_login()
apply_theme()

if "df" not in st.session_state:
    st.warning("No data loaded. Go to the **Upload** page first.")
    st.stop()

df_raw: pd.DataFrame = st.session_state["df"]

page_header("Overview", "Breakage executive summary · all settled-cohort metrics")

filters    = top_filters(df_raw, key_prefix="overview")
currency   = filters["currency"]
date_range = filters["date_range"]
companies  = filters["companies"]

df = apply_filters(df_raw, {
    "date_range": date_range,
    "countries": None,
    "companies": companies or None,
    "currencies": [currency] if currency else None,
})

if df.empty:
    st.warning("No data for this selection.")
    st.stop()

with st.spinner("Analysing data…"):
    k = calculator.kpis(df)
    trend = calculator.monthly_trend_v2(df)
    prelim, threshold_days = calculator.preliminary_months(df)
    deltas = calculator.kpi_deltas(trend, prelim)
breakage_rate = round(100 - k["activation_rate"], 2)

st.markdown("")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(
        "Total Breakage",
        calculator.fmt_amount(k["breakage_amount"], currency),
        delta=f"{calculator.fmt_amount(abs(deltas['breakage_amount_delta']), currency)} vs prev"
        if deltas.get("breakage_amount_delta") is not None else None,
        delta_color="normal",
        help="Total monetary value of cards that were never activated. This is the breakage income — value redeemed but never claimed by the employee.",
    )
with col2:
    st.metric(
        "Breakage Rate",
        f"{breakage_rate}%",
        delta=f"{deltas['breakage_rate_delta']:+.1f}pp vs prev"
        if deltas.get("breakage_rate_delta") is not None else None,
        delta_color="normal",
        help="Breakage Amount ÷ Total Redeemed Amount × 100. Shows what percentage of total redeemed value was never activated.",
    )
with col3:
    st.metric(
        "Total Activated",
        calculator.fmt_amount(k["activated_amount"], currency),
        help="Total monetary value of gift cards that employees successfully activated (clicked and claimed).",
    )
with col4:
    st.metric(
        "Total Redeemed",
        calculator.fmt_amount(k["total_amount"], currency),
        delta=f"{k['breakage_pct']}% is breakage",
        delta_color="off",
        help="Total value of all gift cards issued — both activated and not activated. Breakage + Activated = Total Redeemed.",
    )

st.markdown("")

# ── Trend charts ──────────────────────────────────────────────────────────────
c_left, c_right = st.columns(2)

with c_left:
    section_label("Breakage Rate — Month on Month")
    if len(trend) > 0:
        st.plotly_chart(charts.breakage_trend_exec(trend, prelim), use_container_width=True)
        if prelim:
            st.caption(
                f"Grey = {len(prelim)} preliminary month(s) within {threshold_days}-day window. "
                "Avg uses settled cohorts only."
            )

with c_right:
    section_label("Monthly Breakage Amount")
    fig_ba = px.bar(
        trend,
        x=[charts._fmt_month(m) for m in trend["redemption_month"]],
        y="breakage_amount",
        labels={"x": "", "breakage_amount": f"Amount ({currency})"},
        color_discrete_sequence=["#ff6d05"],
        text=trend["breakage_amount"].map(lambda v: calculator.fmt_amount(v, currency)),
    )
    fig_ba.update_traces(textposition="outside", textfont_size=9, marker_opacity=0.85)
    fig_ba.update_layout(
        margin=dict(t=10, b=40, l=60, r=20),
        plot_bgcolor="white", paper_bgcolor="white", showlegend=False,
    )
    fig_ba.update_yaxes(gridcolor="#f0f0f0")
    fig_ba.update_xaxes(showgrid=False)
    st.plotly_chart(fig_ba, use_container_width=True)

weekly = calculator.weekly_trend(df)
if len(weekly) >= 3:
    section_label("Week-on-Week Breakage Rate")
    st.plotly_chart(charts.weekly_trend_chart(weekly), use_container_width=True)

st.markdown("")

# ── Insights + mini-breakdowns ────────────────────────────────────────────────
ins_col, chart_col = st.columns([3, 2])

with ins_col:
    section_label("Key Insights")
    insights = calculator.generate_insights(df, currency)
    if insights:
        for ins in insights:
            insight_card(f"💡 {ins}")
    else:
        st.info("Not enough data for insights yet.")

with chart_col:
    section_label("Breakage by Card Type")
    ct = calculator.breakage_by_card_type(df)
    if not ct.empty:
        st.plotly_chart(charts.card_type_donut(ct), use_container_width=True)

    section_label("Top Brands by Breakage Rate")
    brand = calculator.breakage_by_brand(df)
    if not brand.empty:
        top8 = brand.nlargest(8, "breakage_rate")
        fig_br = px.bar(
            top8, x="breakage_rate", y="brand", orientation="h",
            labels={"breakage_rate": "Breakage Rate %", "brand": ""},
            color_discrete_sequence=["#654ab7"],
            text=top8["breakage_rate"].map(lambda v: f"{v}%"),
        )
        fig_br.update_traces(textposition="outside", textfont_size=9, marker_opacity=0.85)
        fig_br.update_layout(
            yaxis=dict(autorange="reversed"),
            margin=dict(t=10, b=30, l=10, r=60),
            plot_bgcolor="white", paper_bgcolor="white",
        )
        fig_br.update_xaxes(showgrid=False)
        st.plotly_chart(fig_br, use_container_width=True)
