import pandas as pd
import streamlit as st
from modules import calculator, charts, reporter
from modules.loader import apply_filters, ensure_loaded
from modules.auth import require_login
from modules.ui import apply_theme, page_header, section_label, top_filters

require_login()
apply_theme()

# Clean display charts — no zoom/pan toolbar cluttering the dashboard
PLOTLY_CFG = {"displayModeBar": False, "responsive": True}

ensure_loaded()

df_raw: pd.DataFrame = st.session_state["df"]

page_header("Behavior", "Cohort activation matrix · decay curves · timing · lag distribution")

filters    = top_filters(df_raw, key_prefix="behavior")
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

st.markdown("")

# ── Pending Activation Pipeline ───────────────────────────────────────────────
section_label("Pending Activation Pipeline — Not Yet Activated, by Redemption Month")

pending = calculator.pending_by_month(df)
threshold_days = pending.attrs.get("threshold_days", 60)

st.caption(
    f"For each redemption-month cohort: how many cards are **still not activated** and their value. "
    f"⏳ **In-window** = redeemed within the last {threshold_days} days — these may still convert. "
    f"✔ **Matured** = past the window, so this pending value is effectively confirmed breakage."
)

if pending.empty:
    st.info(f"No data available for {currency}.")
else:
    pend_mode = st.radio(
        "Show values as", ["Card Count", "Currency Amount"],
        horizontal=True, key="pending_mode",
    )
    mode = "count" if pend_mode == "Card Count" else "amount"
    st.plotly_chart(
        charts.pending_pipeline_bar(pending, mode=mode, currency=currency),
        use_container_width=True, config=PLOTLY_CFG,
    )

    # Headline: total still pending while in window
    open_mask = pending["status"] == "In-window"
    open_count = int(pending.loc[open_mask, "pending_count"].sum())
    open_amount = pending.loc[open_mask, "pending_amount"].sum()
    matured_count = int(pending.loc[~open_mask, "pending_count"].sum())
    matured_amount = pending.loc[~open_mask, "pending_amount"].sum()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Pending — in window (cards)", f"{open_count:,}",
              help="Cards not yet activated in cohorts still within the activation window. These may still convert.")
    m2.metric("Pending — in window (amount)", calculator.fmt_amount(open_amount, currency))
    m3.metric("Pending — matured (cards)", f"{matured_count:,}",
              help="Not-activated cards in settled cohorts — effectively confirmed breakage.")
    m4.metric("Pending — matured (amount)", calculator.fmt_amount(matured_amount, currency))

    # Precise month-wise ledger
    table = pending.sort_values("redemption_month", ascending=False).copy()
    table["Month"] = table["redemption_month"].apply(charts._fmt_month)
    table["Pending Amount"] = table["pending_amount"].apply(lambda v: calculator.fmt_amount(v, currency))
    table["% Pending"] = table["pct_pending"].map(lambda v: f"{v}%")
    table["Status"] = table["status"].map({"In-window": "⏳ In-window", "Matured": "✔ Matured"})
    st.dataframe(
        table[["Month", "total", "activated", "pending_count", "Pending Amount", "% Pending", "Status"]].rename(
            columns={"total": "Total Issued", "activated": "Activated", "pending_count": "Still Pending"}
        ),
        use_container_width=True, hide_index=True,
    )

st.markdown("")

# ── Cohort Activation Matrix ──────────────────────────────────────────────────
section_label("Cohort Activation Matrix")
st.caption(
    "Each row = a redemption-month cohort. Each column = the month those cards were activated. "
    "The **Never** column is your breakage. ~ prefix = cohort still within activation window.  \n"
    "**% of Cards** = share of card *count*.  **% of Value** = share of currency *value* "
    "(higher when unactivated cards carry larger denominations).  **Currency Amount** = the value itself."
)

toggle_col, legend_col = st.columns([2, 3])
with toggle_col:
    cohort_mode = st.radio(
        "Show values as",
        ["% of Cards", "% of Value", "Currency Amount"],
        horizontal=True, key="cm_mode",
    )
with legend_col:
    st.markdown(
        "<div style='display:flex;gap:10px;align-items:center;margin-top:8px'>"
        "<span style='background:var(--color-success);color:white;padding:3px 12px;border-radius:var(--radius-xs);font-size:0.8125rem;font-weight:600'>■ Activated</span>"
        "<span style='background:var(--color-error);color:white;padding:3px 12px;border-radius:var(--radius-xs);font-size:0.8125rem;font-weight:600'>■ Breakage (Never)</span>"
        "</div>",
        unsafe_allow_html=True,
    )

with st.spinner("Building cohort matrix…"):
    matrix_data = calculator.cohort_activation_matrix(df, currency)
if matrix_data is None:
    st.info(f"No data available for {currency}.")
else:
    mode = {"% of Cards": "cards", "% of Value": "value", "Currency Amount": "amount"}[cohort_mode]
    st.plotly_chart(charts.cohort_heatmap(matrix_data, mode=mode), use_container_width=True, config=PLOTLY_CFG)

st.markdown("")

# ── Activation Decay ──────────────────────────────────────────────────────────
section_label("Activation Decay — How Quickly Does Each Cohort Activate?")
st.caption(
    "Each line = a redemption cohort. Y-axis = % still unactivated. "
    "Steep early drop = fast cohort. Flat line = high breakage cohort."
)

with st.spinner("Computing decay curves…"):
    survival_df = calculator.cohort_survival(df, currency)
if len(survival_df) >= 2:
    st.plotly_chart(charts.survival_curve_chart(survival_df), use_container_width=True, config=PLOTLY_CFG)
else:
    st.info("Not enough cohort data to show decay curves (need at least 2 cohorts with 5+ records each).")

st.markdown("")

# ── Activation Timing ─────────────────────────────────────────────────────────
section_label("When Do Employees Activate? — Day × Hour Heatmap")
st.caption("Darker = more activations. Useful for understanding email delivery timing and reminder scheduling.")

timing_data = calculator.activation_heatmap_data(df)
if not timing_data.empty:
    st.plotly_chart(charts.activation_timing_heatmap(timing_data), use_container_width=True, config=PLOTLY_CFG)
else:
    st.info("No activation timing data available.")

st.markdown("")

# ── Time to Activate ──────────────────────────────────────────────────────────
section_label("Time to Activate — Distribution")
activated = df[df["is_activated"] & df["activation_lag_days"].notna()]

if len(activated) < 5:
    st.info("Not enough activated cards to show distribution.")
else:
    median_lag = activated["activation_lag_days"].median()
    mean_lag   = activated["activation_lag_days"].mean()
    pct_7      = (activated["activation_lag_days"] <= 7).sum() / len(activated) * 100
    pct_1      = (activated["activation_lag_days"] <= 1).sum() / len(activated) * 100

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "Median days to activate",
        f"{median_lag:.0f}d",
        help="The midpoint: half of all activated cards were claimed within this many days of redemption.",
    )
    c2.metric(
        "Mean days to activate",
        f"{mean_lag:.0f}d",
        help="Average days between redemption and activation. Can be skewed by very late activations — median is usually more representative.",
    )
    c3.metric(
        "Activated within 7 days",
        f"{pct_7:.0f}%",
        help="Percentage of activated cards that were claimed within the first 7 days. High % = employees act quickly on the email.",
    )
    c4.metric(
        "Activated within 24h",
        f"{pct_1:.0f}%",
        help="Percentage of activated cards claimed within 24 hours of redemption — indicates immediate engagement with the email.",
    )

    st.plotly_chart(charts.lag_histogram(df), use_container_width=True, config=PLOTLY_CFG)

st.markdown("---")

# ── Export ────────────────────────────────────────────────────────────────────
with st.expander("📥 Download Behavior Report", expanded=False):
    st.caption(f"Exports cohort matrix, activation timing stats, and lag distribution for **{currency}**.")
    if st.button("Generate & Download", type="primary", key="gen_behavior_report"):
        with st.spinner("Building report…"):
            html = reporter.generate_behavior_report(df, currency, date_range)
        fname = f"behavior_report_{currency}_{pd.Timestamp.now().strftime('%Y%m%d')}.html"
        st.download_button(
            "⬇ Download HTML Report",
            data=html,
            file_name=fname,
            mime="text/html",
            key="dl_behavior_report",
        )
