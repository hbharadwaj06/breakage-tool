import pandas as pd
import streamlit as st
from modules import calculator, charts, reporter
from modules.loader import apply_filters, ensure_loaded
from modules.auth import require_login
from modules.ui import apply_theme, page_header, section_label, insight_card, summary_card, top_filters

require_login()
apply_theme()

ensure_loaded()

df_raw: pd.DataFrame = st.session_state["df"]
available_currencies = sorted(df_raw["Currency"].dropna().unique().tolist())

page_header(
    "Executive Briefing",
    f"Auto-generated insights · {pd.Timestamp.now().strftime('%d %b %Y, %H:%M')}",
)

filters    = top_filters(df_raw, key_prefix="insights", show_currency=False)
date_range = filters["date_range"]
companies  = filters["companies"]

df = apply_filters(df_raw, {
    "date_range": date_range,
    "countries": None,
    "companies": companies or None,
    "currencies": None,
})

if df.empty:
    st.warning("No data for this selection.")
    st.stop()

st.markdown("")


def _render_insights(insights: dict, currency: str):
    if not insights:
        st.info(f"Not enough data to generate insights for {currency}.")
        return
    if insights.get("summary"):
        summary_card(insights["summary"])
    if insights.get("this_month"):
        section_label("This Month")
        for item in insights["this_month"]:
            insight_card(item)
    if insights.get("trends"):
        section_label("Trends")
        for item in insights["trends"]:
            insight_card(item, variant="neutral")
    if insights.get("client_alerts"):
        section_label("Clients to Watch")
        for item in insights["client_alerts"]:
            insight_card(item, variant="alert")
    if insights.get("drivers"):
        section_label("What's Driving Breakage")
        for item in insights["drivers"]:
            insight_card(item)
    if insights.get("forecast"):
        section_label("Forecast")
        insight_card(insights["forecast"], variant="warn")


# ── Multi-currency export ──────────────────────────────────────────────────────
with st.expander("📥 Download Multi-Currency Report", expanded=False):
    top5 = (
        df["Currency"].value_counts()
        .head(5).index.tolist()
    )
    selected_currencies = st.multiselect(
        "Currencies to include",
        options=available_currencies,
        default=[c for c in top5 if c in available_currencies],
        key="report_currencies",
    )
    if st.button("Generate & Download Report", type="primary", key="gen_report"):
        if not selected_currencies:
            st.warning("Select at least one currency.")
        else:
            with st.spinner(f"Generating report for {', '.join(selected_currencies)}…"):
                insights_map = {}
                for curr in selected_currencies:
                    df_c = df[df["Currency"] == curr]
                    if not df_c.empty:
                        insights_map[curr] = calculator.generate_full_insights(df_c, curr)
                html = reporter.generate_multi_currency_report(
                    df, selected_currencies, date_range, insights_map
                )
            fname = f"breakage_report_{'_'.join(selected_currencies)}_{pd.Timestamp.now().strftime('%Y%m%d')}.html"
            st.download_button(
                "⬇ Download HTML Report",
                data=html,
                file_name=fname,
                mime="text/html",
                key="dl_report",
            )

st.markdown("---")

# ── Primary currencies: USD then INR ─────────────────────────────────────────
primary = [c for c in ["USD", "INR"] if c in available_currencies]
others  = [c for c in available_currencies if c not in ["USD", "INR"]]

for i, curr in enumerate(primary):
    if df[df["Currency"] == curr].empty:
        continue
    if i > 0:
        st.markdown('<hr style="border:none;border-top:2px solid var(--neutral-200);margin:32px 0 24px">', unsafe_allow_html=True)
    st.markdown(
        f'<div style="display:inline-block;background:var(--accent);color:white;'
        f'padding:4px 14px;border-radius:var(--radius-pill);font-size:0.8125rem;font-weight:600;'
        f'margin-bottom:16px">{curr}</div>',
        unsafe_allow_html=True,
    )
    with st.spinner(f"Generating {curr} insights…"):
        _render_insights(calculator.generate_full_insights(df, curr), curr)

# ── Other currencies ──────────────────────────────────────────────────────────
if others:
    if primary:
        st.markdown('<hr style="border:none;border-top:2px solid var(--neutral-200);margin:32px 0 24px">', unsafe_allow_html=True)

    st.markdown(
        f'<div style="display:inline-block;background:var(--brand-500);color:white;'
        f'padding:4px 14px;border-radius:var(--radius-pill);font-size:0.8125rem;font-weight:600;'
        f'margin-bottom:8px">Other Currencies</div>',
        unsafe_allow_html=True,
    )
    st.caption("Key breakage metrics. Click **View Full Insights →** to expand a full briefing below.")

    summary_rows = []
    for curr in others:
        df_c = df[df["Currency"] == curr]
        if df_c.empty:
            continue
        k  = calculator.kpis(df_c)
        br = round(100 - k["activation_rate"], 2)
        summary_rows.append({
            "curr": curr,
            "Total Redeemed": calculator.fmt_amount(k["total_amount"], curr),
            "Breakage Amount": calculator.fmt_amount(k["breakage_amount"], curr),
            "Breakage Rate":   f"{br}%",
            "Cards Not Activated": f"{k['breakage_count']:,}",
            "Total Cards":         f"{k['total']:,}",
        })

    if summary_rows:
        st.markdown("")
        hcols = st.columns([0.8, 1.5, 1.5, 1, 1.2, 1, 1.6])
        for col, lbl in zip(hcols, ["Currency", "Total Redeemed", "Breakage Amount",
                                     "Breakage Rate", "Not Activated", "Total Cards", ""]):
            col.markdown(f"<span style='font-size:0.6875rem;font-weight:700;text-transform:uppercase;"
                         f"letter-spacing:0.05em;color:var(--neutral-400)'>{lbl}</span>", unsafe_allow_html=True)
        st.markdown("<hr style='border:none;border-top:1px solid var(--neutral-200);margin:4px 0 10px'>", unsafe_allow_html=True)

        for row in summary_rows:
            cols = st.columns([0.8, 1.5, 1.5, 1, 1.2, 1, 1.6])
            cols[0].markdown(f"`{row['curr']}`")
            cols[1].markdown(row["Total Redeemed"])
            cols[2].markdown(row["Breakage Amount"])
            cols[3].markdown(f"**{row['Breakage Rate']}**")
            cols[4].markdown(row["Cards Not Activated"])
            cols[5].markdown(row["Total Cards"])
            if cols[6].button("View Full Insights →", key=f"_ins_{row['curr']}", use_container_width=True):
                st.session_state["_insights_extra"] = row["curr"]

    extra = st.session_state.get("_insights_extra")
    if extra and extra in others:
        df_extra = df[df["Currency"] == extra]
        if not df_extra.empty:
            st.markdown('<hr style="border:none;border-top:2px solid var(--neutral-200);margin:28px 0 20px">', unsafe_allow_html=True)
            col_title, col_close = st.columns([5, 1])
            col_title.markdown(
                f'<div style="display:inline-block;background:var(--neutral-600);color:white;'
                f'padding:4px 14px;border-radius:var(--radius-pill);font-size:0.8125rem;font-weight:600">'
                f'{extra} — Full Insights</div>',
                unsafe_allow_html=True,
            )
            if col_close.button("✕ Close", key="_ins_close"):
                del st.session_state["_insights_extra"]
                st.rerun()
            with st.spinner(f"Generating {extra} insights…"):
                _render_insights(calculator.generate_full_insights(df, extra), extra)

# ── Micro Trends ──────────────────────────────────────────────────────────────
st.markdown('<hr style="border:none;border-top:2px solid var(--neutral-200);margin:36px 0 28px">', unsafe_allow_html=True)
section_label("Micro Trends — Redemption Behavior Shifts")
st.caption(
    "How card type mix and brand popularity are shifting over time. "
    "Covers all currencies combined."
)

trends_df = calculator.card_type_trends(df)
shift_df  = calculator.brand_shift_trends(df)

if trends_df.empty:
    st.info("Not enough monthly data to show micro trends.")
else:
    tab1, tab2, tab3 = st.tabs([
        "Card Type Mix",
        "Breakage Rate by Card Type",
        "Brand Shifts (Recent 3M vs Prior 3M)",
    ])

    with tab1:
        st.caption("Monthly share of Amazon, Closed Loop, and Open Loop cards.")
        st.plotly_chart(charts.card_type_composition_chart(trends_df), use_container_width=True)

        # Auto insights
        latest  = trends_df[trends_df["month"] == trends_df["month"].max()]
        for _, row in latest.iterrows():
            label = {"amazon": "Amazon", "closed_loop": "Closed Loop", "open_loop": "Open Loop"}.get(row["card_type"], row["card_type"])
            st.markdown(f"- **{label}** accounts for **{row['share_pct']:.1f}%** of redemptions in the latest month")

    with tab2:
        st.caption("Is breakage improving or worsening per card type?")
        st.plotly_chart(charts.card_type_breakage_chart(trends_df), use_container_width=True)

        for _, row in latest.iterrows():
            label = {"amazon": "Amazon", "closed_loop": "Closed Loop", "open_loop": "Open Loop"}.get(row["card_type"], row["card_type"])
            st.markdown(f"- **{label}** breakage rate: **{row['breakage_rate']:.1f}%**")

    with tab3:
        if shift_df.empty:
            st.info("Need at least 6 months of data to show brand shifts.")
        else:
            st.caption("Green = gaining share · Red = losing share vs prior 3 months.")
            st.plotly_chart(charts.brand_shift_chart(shift_df), use_container_width=True)

            top_gainers = shift_df[shift_df["delta"] > 0].head(3)
            top_losers  = shift_df[shift_df["delta"] < 0].tail(3)
            if not top_gainers.empty:
                st.markdown("**Fastest growing brands:**")
                for _, row in top_gainers.iterrows():
                    st.markdown(f"- **{row['Brand']}** +{row['delta']:.2f}pp share")
            if not top_losers.empty:
                st.markdown("**Declining brands:**")
                for _, row in top_losers.sort_values("delta").iterrows():
                    st.markdown(f"- **{row['Brand']}** {row['delta']:.2f}pp share")
