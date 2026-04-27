import pandas as pd
import streamlit as st
from modules import exporter, reporter, calculator
from modules.loader import apply_filters
from modules.auth import require_login
from modules.ui import apply_theme, page_header, section_label, top_filters
from datetime import date

require_login()
apply_theme()

if "df" not in st.session_state:
    st.warning("No data loaded. Go to the **Upload** page first.")
    st.stop()

df_raw: pd.DataFrame = st.session_state["df"]

page_header("Export & Report", "Download Excel data or generate a print-ready PDF briefing")

filters    = top_filters(df_raw, key_prefix="export")
currency   = filters["currency"]
date_range = filters["date_range"]
companies  = filters["companies"]

df = apply_filters(df_raw, {
    "date_range": date_range,
    "countries": None,
    "companies": companies or None,
    "currencies": [currency] if currency else None,
})

st.caption(f"**{len(df):,} records** will be included in both exports · Currency: {currency}")

st.markdown("")

# ── Excel Export ──────────────────────────────────────────────────────────────
section_label("Excel Data Export")

with st.container(border=True):
    st.markdown(
        "Multi-sheet workbook: **Raw Data · Monthly Summary · By Brand · "
        "By Denomination · By Country · By Card Type · Cohort Table**"
    )
    st.markdown("")
    if st.button("Generate Excel", type="primary", key="gen_excel"):
        with st.spinner("Building Excel workbook…"):
            excel_bytes = exporter.build_excel(df)
        filename = f"breakage_{currency}_{date.today().isoformat()}.xlsx"
        st.download_button(
            label="⬇ Download Excel",
            data=excel_bytes,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

st.markdown("")

# ── PDF Report ────────────────────────────────────────────────────────────────
section_label("Executive PDF Report")

with st.container(border=True):
    st.markdown(
        "Formatted HTML report — open in browser and press **Cmd+P → Save as PDF**. "
        "Includes: KPIs, key findings, monthly trend table, client breakdown, cohort table, denomination analysis."
    )
    st.markdown("")
    if st.button("Generate PDF Report", key="gen_pdf"):
        with st.spinner("Building report…"):
            df_report = apply_filters(df_raw, {
                "date_range": date_range,
                "countries": None,
                "companies": companies or None,
                "currencies": [currency],
            })
            insights = calculator.generate_full_insights(df_report, currency)
            html     = reporter.generate_html_report(df_report, currency, date_range, insights)

        filename = f"breakage_report_{currency}_{date.today().isoformat()}.html"
        st.download_button(
            label="⬇ Download HTML Report",
            data=html.encode("utf-8"),
            file_name=filename,
            mime="text/html",
        )
        st.info(
            "Open the downloaded file in your browser → **Cmd+P** (Mac) / **Ctrl+P** (Windows) "
            "→ choose **Save as PDF**."
        )
