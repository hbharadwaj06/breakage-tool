import pandas as pd
import streamlit as st
from modules import calculator
from modules.loader import apply_filters
from modules.auth import require_login
from modules.ui import apply_theme, page_header, section_label, insight_card, summary_card, top_filters

require_login()
apply_theme()

if "df" not in st.session_state:
    st.warning("No data loaded. Go to the **Upload** page first.")
    st.stop()

df_raw: pd.DataFrame = st.session_state["df"]
available_currencies = sorted(df_raw["Currency"].dropna().unique().tolist())

page_header(
    "Executive Briefing",
    f"Auto-generated insights · {pd.Timestamp.now().strftime('%d %b %Y, %H:%M')}",
)

filters    = top_filters(df_raw, key_prefix="insights", show_currency=False)
date_range = filters["date_range"]
companies  = filters["companies"]

# Filter by date + company only — currency handled per section below
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


# ── Primary currencies: USD then INR ─────────────────────────────────────────
primary = [c for c in ["USD", "INR"] if c in available_currencies]
others  = [c for c in available_currencies if c not in ["USD", "INR"]]

for i, curr in enumerate(primary):
    if df[df["Currency"] == curr].empty:
        continue
    if i > 0:
        st.markdown("""
        <hr style="border:none;border-top:2px solid var(--neutral-200);margin:32px 0 24px">
        """, unsafe_allow_html=True)
    st.markdown(
        f'<div style="display:inline-block;background:var(--accent);color:white;'
        f'padding:4px 14px;border-radius:var(--radius-pill);font-size:0.8125rem;font-weight:600;'
        f'margin-bottom:16px">{curr}</div>',
        unsafe_allow_html=True,
    )
    with st.spinner(f"Generating {curr} insights…"):
        _render_insights(calculator.generate_full_insights(df, curr), curr)

# ── Other currencies summary table ────────────────────────────────────────────
if others:
    if primary:
        st.markdown("""
        <hr style="border:none;border-top:2px solid var(--neutral-200);margin:32px 0 24px">
        """, unsafe_allow_html=True)

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
        st.markdown("<hr style='border:none;border-top:1px solid var(--neutral-200);margin:4px 0 10px'>",
                    unsafe_allow_html=True)

        for row in summary_rows:
            cols = st.columns([0.8, 1.5, 1.5, 1, 1.2, 1, 1.6])
            cols[0].markdown(f"`{row['curr']}`")
            cols[1].markdown(row["Total Redeemed"])
            cols[2].markdown(row["Breakage Amount"])
            cols[3].markdown(f"**{row['Breakage Rate']}**")
            cols[4].markdown(row["Cards Not Activated"])
            cols[5].markdown(row["Total Cards"])
            if cols[6].button("View Full Insights →", key=f"_ins_{row['curr']}",
                              use_container_width=True):
                st.session_state["_insights_extra"] = row["curr"]

    # ── Expanded insights for selected currency ────────────────────────────────
    extra = st.session_state.get("_insights_extra")
    if extra and extra in others:
        df_extra = df[df["Currency"] == extra]
        if not df_extra.empty:
            st.markdown("""
            <hr style="border:none;border-top:2px solid var(--neutral-200);margin:28px 0 20px">
            """, unsafe_allow_html=True)
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
