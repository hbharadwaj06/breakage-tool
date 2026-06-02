import pandas as pd
import streamlit as st
from modules import calculator, fx
from modules.loader import apply_filters, ensure_loaded
from modules.auth import require_login
from modules.ui import apply_theme, page_header, section_label, top_filters

require_login()
apply_theme()

ensure_loaded()

df_raw: pd.DataFrame = st.session_state["df"]
available_currencies = sorted(df_raw["Currency"].dropna().unique().tolist())

page_header("Global View", "All currencies consolidated into a single number · live exchange rates")

# Date + company filters only — no currency filter (we want everything)
filters    = top_filters(df_raw, key_prefix="global", show_currency=False)
date_range = filters["date_range"]
companies  = filters["companies"]

df_global = apply_filters(df_raw, {
    "date_range": date_range,
    "countries": None,
    "companies": companies or None,
    "currencies": None,
})

if df_global.empty:
    st.warning("No data for this selection.")
    st.stop()

st.markdown("")

# ── Base currency selector ────────────────────────────────────────────────────
section_label("Consolidate Into")

primary_opts = [c for c in ["USD", "INR"] if c in available_currencies]
other_opts   = [c for c in available_currencies if c not in ["USD", "INR"]]

sel_col, rate_col = st.columns([3, 5])
with sel_col:
    base_choice = st.radio(
        "Base currency", primary_opts + (["Other…"] if other_opts else []),
        horizontal=True, key="global_base_radio",
    )
    if base_choice == "Other…":
        base_currency = st.selectbox("Pick currency", other_opts, key="global_base_other")
    else:
        base_currency = base_choice

# ── Fetch rates ───────────────────────────────────────────────────────────────
rates, rate_err = fx.fetch_rates()

with rate_col:
    if rate_err:
        st.warning(rate_err)
        with st.expander("Enter rates manually (how many units of each currency = 1 USD)"):
            currencies_in_data = df_global["Currency"].dropna().unique().tolist()
            manual = {}
            cols = st.columns(min(len(currencies_in_data), 4))
            for i, cur in enumerate(currencies_in_data):
                default = 1.0 if cur == "USD" else 0.0
                manual[cur] = cols[i % 4].number_input(
                    f"{cur} / USD", value=default, min_value=0.0, step=0.01,
                    key=f"manual_rate_{cur}",
                )
            if any(v > 0 for v in manual.values()):
                rates = manual
    else:
        st.caption(
            f"Live rates · 1 USD = {rates.get(base_currency, '–')} {base_currency} "
            f"· Source: open.er-api.com · Updated daily"
        )

st.markdown("")

# ── Consolidated KPIs ─────────────────────────────────────────────────────────
section_label("Consolidated Totals")

rows        = fx.consolidate(df_global, base_currency, rates)
convertible = [r for r in rows if r["convertible"]]
skipped     = [r["currency"] for r in rows if not r["convertible"]]

total_breakage_conv = sum(r["conv_breakage"] for r in convertible)
total_redeemed_conv = sum(r["conv_total"]    for r in convertible)
total_cards         = len(df_global)
breakage_cards      = int(df_global["is_breakage"].sum())
overall_rate        = round(breakage_cards / total_cards * 100, 2) if total_cards else 0

m1, m2, m3, m4 = st.columns(4)
m1.metric(
    f"Total Breakage ({base_currency})",
    calculator.fmt_amount(total_breakage_conv, base_currency),
    help=f"Sum of breakage amounts across all currencies, each converted to {base_currency} using today's live exchange rates.",
)
m2.metric(
    f"Total Redeemed ({base_currency})",
    calculator.fmt_amount(total_redeemed_conv, base_currency),
    help=f"Sum of all redeemed amounts across all currencies, converted to {base_currency}. Breakage + Activated = Total Redeemed.",
)
m3.metric(
    "Overall Breakage Rate",
    f"{overall_rate}%",
    help="Cards not activated ÷ total cards, across all currencies. A card-count ratio — not affected by exchange rates or currency mix.",
)
m4.metric(
    "Cards Not Activated",
    f"{breakage_cards:,}",
    help="Total number of individual gift cards that were never activated, across all currencies and servers.",
)

if skipped:
    st.caption(f"⚠ Could not convert: {', '.join(skipped)} — not found in rates table.")

st.markdown("")

# ── Per-currency breakdown table ──────────────────────────────────────────────
section_label("Per-Currency Breakdown")
st.caption("Original amounts alongside their converted equivalent. Sorted by breakage amount (highest first).")

table_rows = []
for r in rows:
    table_rows.append({
        "Currency":                        r["currency"],
        "Total Redeemed (original)":       calculator.fmt_amount(r["orig_total"],    r["currency"]),
        "Breakage (original)":             calculator.fmt_amount(r["orig_breakage"], r["currency"]),
        f"Total Redeemed ({base_currency})":  calculator.fmt_amount(r["conv_total"],    base_currency) if r["convertible"] else "—",
        f"Breakage ({base_currency})":        calculator.fmt_amount(r["conv_breakage"], base_currency) if r["convertible"] else "—",
    })

st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

st.markdown("")

# ── Currency mix chart ────────────────────────────────────────────────────────
section_label("Breakage Mix by Currency")
st.caption(f"Share of total consolidated breakage contributed by each currency (in {base_currency}).")

if convertible:
    import plotly.express as px
    pie_df = pd.DataFrame([
        {"Currency": r["currency"], "Breakage": round(r["conv_breakage"], 2)}
        for r in convertible if r["conv_breakage"] > 0
    ])
    fig = px.pie(
        pie_df, names="Currency", values="Breakage",
        color_discrete_sequence=["#ff6d05", "#5b3b97", "#29294c", "#f04438", "#f79009",
                                  "#7a56bd", "#0ba5ec", "#12b76a", "#a086d0"],
        hole=0.45,
    )
    fig.update_traces(textposition="outside", textinfo="percent+label")
    fig.update_layout(
        showlegend=True,
        margin=dict(t=20, b=20, l=20, r=20),
        paper_bgcolor="white",
    )
    st.plotly_chart(fig, use_container_width=True)
