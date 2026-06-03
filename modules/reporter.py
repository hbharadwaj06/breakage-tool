import pandas as pd
from modules import calculator


def _kpi_box(label, value, sub=""):
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    return (
        f'<div class="kpi-box">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>'
        f'{sub_html}</div>'
    )


def _table_html(df: pd.DataFrame, max_rows: int = 20) -> str:
    subset = df.head(max_rows)
    header = "".join(f"<th>{c}</th>" for c in subset.columns)
    rows = ""
    for _, row in subset.iterrows():
        cells = "".join(f"<td>{v}</td>" for v in row.values)
        rows += f"<tr>{cells}</tr>"
    return f"<table><thead><tr>{header}</tr></thead><tbody>{rows}</tbody></table>"


def _section(title, body, page_break=True):
    pb = 'style="page-break-before: always;"' if page_break else ""
    return f'<div class="section" {pb}><h2>{title}</h2>{body}</div>'


def _insights_html(items, color="#008000"):
    if not items:
        return "<p><em>No findings for this section.</em></p>"
    return "".join(
        f'<div class="insight" style="border-left-color:{color}">{i}</div>'
        for i in items
    )


def generate_html_report(df: pd.DataFrame, currency: str, date_range: tuple, insights: dict) -> str:
    k = calculator.kpis(df)
    trend = calculator.monthly_trend_v2(df)
    company_df = calculator.breakage_by_company(df)
    cohort_df = calculator.cohort_table(df)
    denom_df = calculator.breakage_by_denomination(df, currency=currency)
    breakage_rate = round(100 - k["activation_rate"], 2)
    period = f"{date_range[0]} to {date_range[1]}" if date_range else "All periods"
    generated = pd.Timestamp.now().strftime("%d %b %Y, %H:%M")

    # Build trend display table
    trend_d = trend.copy()
    trend_d["breakage_rate"] = (100 - trend_d["activation_rate"]).round(2).map(lambda v: f"{v}%")
    trend_d["activation_rate"] = trend_d["activation_rate"].map(lambda v: f"{v}%")
    trend_d["breakage_amount"] = trend_d["breakage_amount"].map(lambda v: calculator.fmt_amount(v, currency))
    trend_d = trend_d.rename(columns={
        "redemption_month": "Month", "total": "Total", "activated": "Activated",
        "breakage_count": "Breakage Count", "breakage_amount": "Breakage Amount",
        "activation_rate": "Act. Rate", "breakage_rate": "Breakage Rate",
    })[["Month", "Total", "Activated", "Act. Rate", "Breakage Count", "Breakage Amount", "Breakage Rate"]]

    # Build company display table
    co_d = company_df.head(15).copy()
    co_d["breakage_amount"] = co_d["breakage_amount"].map(lambda v: calculator.fmt_amount(v, currency))
    co_d["breakage_rate"] = co_d["breakage_rate"].map(lambda v: f"{v}%")
    co_d = co_d.rename(columns={
        "company": "Company", "total_count": "Total", "breakage_count": "Breakage Cards",
        "breakage_amount": "Breakage Amount", "breakage_rate": "Rate",
    })[["Company", "Total", "Breakage Cards", "Breakage Amount", "Rate"]]

    # Build KPI row
    kpi_row = (
        '<div class="kpi-row">'
        + _kpi_box("Total Breakage", calculator.fmt_amount(k["breakage_amount"], currency), f"{k['breakage_count']:,} cards")
        + _kpi_box("Breakage Rate", f"{breakage_rate}%", "of all redemptions")
        + _kpi_box("Total Activated", calculator.fmt_amount(k["activated_amount"], currency), f"{k['activated']:,} cards")
        + _kpi_box("Total Redeemed", calculator.fmt_amount(k["total_amount"], currency), f"{k['total']:,} cards")
        + "</div>"
    )

    summary_block = f'<div class="summary-para">{insights.get("summary", "")}</div>'

    # Insights sections
    this_month_html = _insights_html(insights.get("this_month", []))
    trends_html = _insights_html(insights.get("trends", []), "#2980b9")
    clients_html = _insights_html(insights.get("client_alerts", []), "#c0392b")
    drivers_html = _insights_html(insights.get("drivers", []))
    forecast_block = ""
    if insights.get("forecast"):
        forecast_block = (
            "<h3>Forecast</h3>"
            + _insights_html([insights["forecast"]], "#f39c12")
        )

    findings_body = (
        "<h3>This Month</h3>" + this_month_html
        + "<h3>Trends</h3>" + trends_html
        + "<h3>Clients to Watch</h3>" + clients_html
        + "<h3>What's Driving Breakage</h3>" + drivers_html
        + forecast_block
    )

    css = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
       font-size: 13px; color: #1a1a1a; background: white; }
.cover { display: flex; flex-direction: column; justify-content: center; align-items: flex-start;
         min-height: 100vh; padding: 80px 60px; background: #f8f9fa; page-break-after: always; }
.cover h1 { font-size: 32px; font-weight: 700; color: #008000; margin-bottom: 12px; }
.cover .sub { font-size: 16px; color: #555; margin-bottom: 6px; }
.cover .meta { margin-top: 40px; font-size: 12px; color: #888; }
.section { padding: 40px 60px; }
h2 { font-size: 18px; font-weight: 700; color: #008000; border-bottom: 2px solid #008000;
     padding-bottom: 8px; margin-bottom: 20px; text-transform: uppercase; letter-spacing: 0.05em; }
h3 { font-size: 14px; font-weight: 600; color: #333; margin: 20px 0 10px; }
.kpi-row { display: flex; gap: 20px; margin-bottom: 24px; flex-wrap: wrap; }
.kpi-box { flex: 1; min-width: 140px; background: #f8f9fa; border-top: 3px solid #008000;
           padding: 16px; border-radius: 4px; }
.kpi-label { font-size: 10px; text-transform: uppercase; letter-spacing: 0.08em;
             color: #888; margin-bottom: 6px; }
.kpi-value { font-size: 22px; font-weight: 700; color: #1a1a1a; }
.kpi-sub { font-size: 11px; color: #888; margin-top: 4px; }
.insight { background: #f8f9fa; border-left: 4px solid #008000; padding: 12px 16px;
           margin-bottom: 10px; border-radius: 2px; line-height: 1.6; font-size: 13px; }
.summary-para { font-size: 14px; line-height: 1.8; color: #333; background: #f0f7f0;
                border-left: 4px solid #008000; padding: 16px 20px; border-radius: 4px;
                margin-bottom: 24px; }
table { width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 12px; }
th { background: #008000; color: white; padding: 8px 10px; text-align: left;
     font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; }
td { padding: 7px 10px; border-bottom: 1px solid #f0f0f0; }
tr:nth-child(even) td { background: #fafafa; }
.footer { padding: 20px 60px; font-size: 11px; color: #aaa; border-top: 1px solid #f0f0f0; }
@media print {
  body { font-size: 12px; }
  .cover { min-height: auto; padding: 60px 40px; }
  .section { padding: 30px 40px; }
  @page { margin: 0; size: A4; }
}
"""

    cover = (
        '<div class="cover">'
        f'<h1>Breakage Analysis Report</h1>'
        f'<div class="sub">Currency: <strong>{currency}</strong></div>'
        f'<div class="sub">Period: <strong>{period}</strong></div>'
        f'<div class="sub">Total Records: <strong>{k["total"]:,}</strong></div>'
        f'<div class="meta">Generated: {generated} &nbsp;·&nbsp; Vantage Circle</div>'
        '</div>'
    )

    html = (
        '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        f'<title>Breakage Analysis Report — {currency}</title>'
        f'<style>{css}</style></head><body>'
        + cover
        + _section("Executive Summary", summary_block + kpi_row, page_break=False)
        + _section("Key Findings", findings_body)
        + _section("Monthly Trend", _table_html(trend_d, 30))
        + _section("Client Breakdown", _table_html(co_d, 20))
        + _section(
            "Cohort Activation Table",
            "<p style='margin-bottom:12px;font-size:12px;color:#555'>"
            "% of each redemption-month cohort activated within N days.</p>"
            + _table_html(cohort_df, 20),
        )
        + _section("Breakage by Denomination", _table_html(denom_df, 10))
        + f'<div class="footer">Breakage Analysis &nbsp;·&nbsp; {currency} &nbsp;·&nbsp; {period} &nbsp;·&nbsp; {generated}</div>'
        + '</body></html>'
    )

    return html


def _currency_section(df: pd.DataFrame, currency: str, insights: dict, period: str) -> str:
    """One currency block for the multi-currency report."""
    k = calculator.kpis(df)
    breakage_rate = round(100 - k["activation_rate"], 2)
    trend = calculator.monthly_trend_v2(df)

    trend_d = trend.copy()
    trend_d["breakage_rate"]   = (100 - trend_d["activation_rate"]).round(2).map(lambda v: f"{v}%")
    trend_d["activation_rate"] = trend_d["activation_rate"].map(lambda v: f"{v}%")
    trend_d["breakage_amount"] = trend_d["breakage_amount"].map(lambda v: calculator.fmt_amount(v, currency))
    trend_d = trend_d.rename(columns={
        "redemption_month": "Month", "total": "Total", "activated": "Activated",
        "breakage_count": "Not Activated", "breakage_amount": "Breakage Amount",
        "activation_rate": "Act. Rate", "breakage_rate": "Breakage Rate",
    })[["Month", "Total", "Activated", "Act. Rate", "Not Activated", "Breakage Amount", "Breakage Rate"]]

    kpi_row = (
        '<div class="kpi-row">'
        + _kpi_box("Breakage", calculator.fmt_amount(k["breakage_amount"], currency), f"{k['breakage_count']:,} cards")
        + _kpi_box("Breakage Rate", f"{breakage_rate}%")
        + _kpi_box("Activated", calculator.fmt_amount(k["activated_amount"], currency), f"{k['activated']:,} cards")
        + _kpi_box("Total", calculator.fmt_amount(k["total_amount"], currency), f"{k['total']:,} cards")
        + "</div>"
    )

    summary = f'<div class="summary-para">{insights.get("summary", "Insufficient data.")}</div>' if insights else ""
    findings = ""
    for section, color in [("this_month", "#008000"), ("trends", "#2980b9"),
                            ("client_alerts", "#c0392b"), ("drivers", "#008000")]:
        items = insights.get(section, []) if insights else []
        if items:
            label = {"this_month": "This Month", "trends": "Trends",
                     "client_alerts": "Clients to Watch", "drivers": "Drivers"}.get(section, section)
            findings += f"<h3>{label}</h3>" + _insights_html(items, color)
    if insights and insights.get("forecast"):
        findings += "<h3>Forecast</h3>" + _insights_html([insights["forecast"]], "#f39c12")

    body = summary + kpi_row
    if findings:
        body += f'<div style="margin-top:20px">{findings}</div>'
    body += "<h3 style='margin-top:24px'>Monthly Trend</h3>" + _table_html(trend_d, 24)

    return (
        f'<div class="currency-section" style="page-break-before:always">'
        f'<div class="currency-badge">{currency}</div>'
        + body
        + '</div>'
    )


def generate_multi_currency_report(
    df: pd.DataFrame,
    currencies: list,
    date_range: tuple,
    insights_map: dict,
) -> str:
    """Combined HTML report covering multiple currencies."""
    period    = f"{date_range[0]} to {date_range[1]}" if date_range else "All periods"
    generated = pd.Timestamp.now().strftime("%d %b %Y, %H:%M")

    # Cross-currency summary table
    summary_rows = []
    for curr in currencies:
        df_c = df[df["Currency"] == curr]
        if df_c.empty:
            continue
        k  = calculator.kpis(df_c)
        br = round(100 - k["activation_rate"], 2)
        summary_rows.append({
            "Currency": curr,
            "Total Cards": f"{k['total']:,}",
            "Breakage Cards": f"{k['breakage_count']:,}",
            "Breakage Rate": f"{br}%",
            "Breakage Amount": calculator.fmt_amount(k["breakage_amount"], curr),
            "Activated Amount": calculator.fmt_amount(k["activated_amount"], curr),
        })
    summary_df = pd.DataFrame(summary_rows)

    css = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
       font-size: 13px; color: #1a1a1a; background: white; }
.cover { display:flex; flex-direction:column; justify-content:center; align-items:flex-start;
         min-height:100vh; padding:80px 60px; background:linear-gradient(135deg,#1a0f2e,#2d1b4e); }
.cover h1 { font-size:36px; font-weight:800; color:#ffffff; margin-bottom:12px; letter-spacing:-0.02em; }
.cover .sub { font-size:15px; color:rgba(255,255,255,0.65); margin-bottom:6px; }
.cover .meta { margin-top:48px; font-size:12px; color:rgba(255,255,255,0.35); }
.cover .badge-row { display:flex; gap:10px; flex-wrap:wrap; margin-top:28px; }
.cover .cbadge { background:rgba(255,255,255,0.12); color:#fff; border:1px solid rgba(255,255,255,0.2);
                 padding:6px 16px; border-radius:20px; font-size:13px; font-weight:600; }
.currency-section { padding:40px 60px; }
.currency-badge { display:inline-block; background:#5b3b97; color:white; padding:5px 18px;
                  border-radius:20px; font-size:14px; font-weight:700; margin-bottom:20px;
                  letter-spacing:0.04em; }
h2 { font-size:18px; font-weight:700; color:#5b3b97; border-bottom:2px solid #5b3b97;
     padding-bottom:8px; margin-bottom:20px; text-transform:uppercase; letter-spacing:0.05em; }
h3 { font-size:13px; font-weight:600; color:#333; margin:18px 0 8px; }
.kpi-row { display:flex; gap:16px; margin-bottom:20px; flex-wrap:wrap; }
.kpi-box { flex:1; min-width:130px; background:#f6f4fb; border-top:3px solid #5b3b97;
           padding:14px; border-radius:6px; }
.kpi-label { font-size:10px; text-transform:uppercase; letter-spacing:0.08em; color:#888; margin-bottom:4px; }
.kpi-value { font-size:20px; font-weight:700; color:#1a1a1a; }
.kpi-sub { font-size:11px; color:#888; margin-top:3px; }
.insight { background:#f6f4fb; border-left:4px solid #5b3b97; padding:10px 14px;
           margin-bottom:8px; border-radius:3px; line-height:1.6; font-size:12.5px; }
.summary-para { font-size:13px; line-height:1.8; color:#333; background:#f6f4fb;
                border-left:4px solid #ff6d05; padding:14px 18px; border-radius:4px; margin-bottom:20px; }
table { width:100%; border-collapse:collapse; margin-top:10px; font-size:12px; }
th { background:#5b3b97; color:white; padding:8px 10px; text-align:left;
     font-weight:600; font-size:11px; text-transform:uppercase; letter-spacing:0.05em; }
td { padding:7px 10px; border-bottom:1px solid #f0f0f0; }
tr:nth-child(even) td { background:#fafafa; }
.overview-section { padding:40px 60px; }
.footer { padding:16px 60px; font-size:11px; color:#aaa; border-top:1px solid #f0f0f0; margin-top:20px; }
@media print { @page { margin:0; size:A4; } }
"""

    badge_row = "".join(f'<span class="cbadge">{c}</span>' for c in currencies)
    cover = (
        '<div class="cover">'
        '<h1>Breakage Analysis<br>Multi-Currency Report</h1>'
        f'<div class="sub">Period: <strong style="color:white">{period}</strong></div>'
        f'<div class="badge-row">{badge_row}</div>'
        f'<div class="meta">Generated: {generated} &nbsp;·&nbsp; Vantage Circle · Internal</div>'
        '</div>'
    )

    overview = (
        '<div class="overview-section">'
        '<h2>Cross-Currency Overview</h2>'
        + _table_html(summary_df, len(summary_df))
        + '</div>'
    )

    currency_sections = ""
    for curr in currencies:
        df_c = df[df["Currency"] == curr]
        if df_c.empty:
            continue
        currency_sections += _currency_section(df_c, curr, insights_map.get(curr, {}), period)

    footer = (
        f'<div class="footer">Breakage Analysis · Multi-Currency Report · {period} · {generated}</div>'
    )

    return (
        '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        f'<title>Breakage Report — Multi-Currency</title>'
        f'<style>{css}</style></head><body>'
        + cover + overview + currency_sections + footer
        + '</body></html>'
    )


def _cohort_matrix_html(matrix: dict) -> str:
    """Build a rich HTML table from cohort_activation_matrix() output.
    Each cell shows percentage on top and currency value below."""
    row_labels   = matrix["row_labels"]
    act_cols     = matrix["act_cols"]
    pct_text     = matrix["act_pct_text"]
    amt_text     = matrix["act_amount_text"]
    never_pct    = matrix["never_pct_text"]
    never_amt    = matrix["never_amount_text"]
    open_cohorts = matrix["open_cohorts"]

    # Header
    header_cells = '<th class="cm-rh">Redemption Month</th>'
    for col in act_cols:
        header_cells += f'<th class="cm-ah">{col}</th>'
    header_cells += '<th class="cm-nh">Never (Breakage)</th>'

    rows_html = ""
    for i, r_month in enumerate(row_labels):
        is_open = r_month in open_cohorts
        row_class = "cm-open" if is_open else ""
        prefix    = "~" if is_open else ""
        cells = f'<td class="cm-label">{prefix}{r_month}</td>'

        for j, col in enumerate(act_cols):
            p = pct_text[i][j] if j < len(pct_text[i]) else ""
            a = amt_text[i][j] if j < len(amt_text[i]) else ""
            if p:
                cells += (
                    f'<td class="cm-act">'
                    f'<span class="cm-pct">{p}</span>'
                    f'<span class="cm-amt">{a}</span>'
                    f'</td>'
                )
            else:
                cells += '<td class="cm-empty"></td>'

        np_ = never_pct[i][0]  if never_pct[i]  else ""
        na_ = never_amt[i][0]  if never_amt[i]  else ""
        cells += (
            f'<td class="cm-never">'
            f'<span class="cm-pct">{np_}</span>'
            f'<span class="cm-amt">{na_}</span>'
            f'</td>'
        )

        rows_html += f'<tr class="{row_class}">{cells}</tr>'

    return f"""
<div class="cm-wrap">
<table class="cm-table">
  <thead><tr>{header_cells}</tr></thead>
  <tbody>{rows_html}</tbody>
</table>
</div>"""


def generate_behavior_report(df: pd.DataFrame, currency: str, date_range: tuple) -> str:
    """HTML report for the Behavior page: cohort matrix (% + amount), lag stats, trend."""
    period    = f"{date_range[0]} to {date_range[1]}" if date_range else "All periods"
    generated = pd.Timestamp.now().strftime("%d %b %Y, %H:%M")

    activated = df[df["is_activated"] & df["activation_lag_days"].notna()]

    # ── Lag stats ──────────────────────────────────────────────────────────────
    if len(activated) >= 5:
        median_lag = activated["activation_lag_days"].median()
        mean_lag   = activated["activation_lag_days"].mean()
        pct_7      = (activated["activation_lag_days"] <= 7).sum() / len(activated) * 100
        pct_1      = (activated["activation_lag_days"] <= 1).sum() / len(activated) * 100
        lag_kpis = (
            '<div class="kpi-row">'
            + _kpi_box("Median Days to Activate", f"{median_lag:.0f}d")
            + _kpi_box("Mean Days to Activate",   f"{mean_lag:.0f}d")
            + _kpi_box("Activated Within 7 Days", f"{pct_7:.0f}%")
            + _kpi_box("Activated Within 24h",    f"{pct_1:.0f}%")
            + '</div>'
        )
        buckets = [
            ("Same day (0d)",  (activated["activation_lag_days"] == 0).sum()),
            ("1–7 days",       ((activated["activation_lag_days"] >= 1) & (activated["activation_lag_days"] <= 7)).sum()),
            ("8–30 days",      ((activated["activation_lag_days"] >= 8) & (activated["activation_lag_days"] <= 30)).sum()),
            ("31–90 days",     ((activated["activation_lag_days"] >= 31) & (activated["activation_lag_days"] <= 90)).sum()),
            ("91–180 days",    ((activated["activation_lag_days"] >= 91) & (activated["activation_lag_days"] <= 180)).sum()),
            ("180+ days",      (activated["activation_lag_days"] > 180).sum()),
        ]
        bucket_df = pd.DataFrame(buckets, columns=["Window", "Cards"])
        bucket_df["% of Activated"] = (bucket_df["Cards"] / len(activated) * 100).round(1).map(lambda v: f"{v}%")
        lag_section = _section(
            "Time to Activate",
            lag_kpis + "<h3>Distribution by Window</h3>" + _table_html(bucket_df, 10),
            page_break=False,
        )
    else:
        lag_section = ""

    # ── Cohort activation matrix (% + currency) ────────────────────────────────
    matrix = calculator.cohort_activation_matrix(df, currency)
    if matrix:
        cohort_note = (
            "<p style='margin-bottom:12px;font-size:12px;color:#555'>"
            "Each row = a redemption-month cohort. Each column = the month those cards were activated. "
            "<strong>Top line</strong> = % of cohort · <strong>Bottom line</strong> = currency amount. "
            "~ prefix = cohort still within the activation window (preliminary).</p>"
        )
        legend = (
            '<div style="display:flex;gap:16px;margin-bottom:14px;font-size:11px;font-weight:600">'
            '<span style="display:flex;align-items:center;gap:5px">'
            '<span style="width:12px;height:12px;background:#d4edda;border:1px solid #28a745;border-radius:2px;display:inline-block"></span>'
            'Activated</span>'
            '<span style="display:flex;align-items:center;gap:5px">'
            '<span style="width:12px;height:12px;background:#f8d7da;border:1px solid #dc3545;border-radius:2px;display:inline-block"></span>'
            'Breakage (Never)</span>'
            '</div>'
        )
        cohort_section = _section(
            "Cohort Activation Matrix",
            cohort_note + legend + _cohort_matrix_html(matrix),
        )
    else:
        cohort_section = _section(
            "Cohort Activation Matrix",
            f"<p>No cohort data available for {currency}.</p>",
        )

    # ── Monthly trend ──────────────────────────────────────────────────────────
    trend = calculator.monthly_trend_v2(df)
    trend_d = trend.copy()
    trend_d["breakage_rate"]   = (100 - trend_d["activation_rate"]).round(2).map(lambda v: f"{v}%")
    trend_d["activation_rate"] = trend_d["activation_rate"].map(lambda v: f"{v}%")
    trend_d["breakage_amount"] = trend_d["breakage_amount"].map(lambda v: calculator.fmt_amount(v, currency))
    trend_d = trend_d.rename(columns={
        "redemption_month": "Month", "total": "Total", "activated": "Activated",
        "breakage_count": "Not Activated", "breakage_amount": "Breakage Amount",
        "activation_rate": "Act. Rate", "breakage_rate": "Breakage Rate",
    })[["Month", "Total", "Activated", "Act. Rate", "Not Activated", "Breakage Amount", "Breakage Rate"]]
    trend_section = _section("Monthly Trend", _table_html(trend_d, 30))

    css = """
* { box-sizing:border-box; margin:0; padding:0; }
body { font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;
       font-size:13px; color:#1a1a1a; background:white; }
.cover { display:flex; flex-direction:column; justify-content:center; align-items:flex-start;
         min-height:55vh; padding:60px 60px; background:linear-gradient(135deg,#1a0f2e,#2d1b4e); }
.cover h1 { font-size:30px; font-weight:800; color:#fff; margin-bottom:10px; letter-spacing:-0.02em; }
.cover .sub { font-size:14px; color:rgba(255,255,255,0.6); margin-bottom:5px; }
.cover .meta { margin-top:36px; font-size:11px; color:rgba(255,255,255,0.3); }
.section { padding:36px 60px; }
h2 { font-size:17px; font-weight:700; color:#5b3b97; border-bottom:2px solid #5b3b97;
     padding-bottom:7px; margin-bottom:18px; text-transform:uppercase; letter-spacing:0.05em; }
h3 { font-size:13px; font-weight:600; color:#333; margin:16px 0 8px; }
.kpi-row { display:flex; gap:16px; margin-bottom:16px; flex-wrap:wrap; }
.kpi-box { flex:1; min-width:130px; background:#f6f4fb; border-top:3px solid #5b3b97;
           padding:14px; border-radius:6px; }
.kpi-label { font-size:10px; text-transform:uppercase; letter-spacing:0.08em; color:#888; margin-bottom:4px; }
.kpi-value { font-size:22px; font-weight:700; color:#1a1a1a; }
.kpi-sub { font-size:11px; color:#888; margin-top:3px; }

/* Standard tables */
table { border-collapse:collapse; margin-top:10px; font-size:12px; }
th { background:#5b3b97; color:white; padding:7px 10px; text-align:left;
     font-weight:600; font-size:11px; text-transform:uppercase; letter-spacing:0.04em; }
td { padding:6px 10px; border-bottom:1px solid #f0f0f0; }
tr:nth-child(even) td { background:#fafafa; }

/* Cohort matrix */
.cm-wrap { overflow-x:auto; margin-top:8px; }
.cm-table { width:auto; border-collapse:collapse; font-size:11px; white-space:nowrap; }
.cm-table thead tr th { background:#5b3b97; color:white; padding:6px 10px;
                        font-size:10px; text-transform:uppercase; letter-spacing:0.04em; }
.cm-rh  { min-width:110px; position:sticky; left:0; z-index:2; background:#5b3b97; }
.cm-ah  { min-width:90px; text-align:center; }
.cm-nh  { min-width:110px; text-align:center; background:#7f1d1d !important; }
.cm-label { font-weight:600; background:#f6f4fb; position:sticky; left:0; z-index:1;
            padding:6px 10px; border-bottom:1px solid #e8e4f4; font-size:11px; }
.cm-open .cm-label { color:#6b21a8; }
.cm-act   { background:#d4edda; text-align:center; padding:4px 8px;
            border-bottom:1px solid #c3e6cb; vertical-align:middle; }
.cm-never { background:#f8d7da; text-align:center; padding:4px 8px;
            border-bottom:1px solid #f5c6cb; vertical-align:middle; }
.cm-empty { background:#fafafa; border-bottom:1px solid #f0f0f0; }
.cm-pct { display:block; font-weight:700; font-size:11px; color:#1a1a1a; }
.cm-never .cm-pct { color:#721c24; }
.cm-amt { display:block; font-size:9.5px; color:#555; margin-top:1px; }
.cm-never .cm-amt { color:#a94442; }

.footer { padding:14px 60px; font-size:11px; color:#aaa; border-top:1px solid #f0f0f0; }
@media print { @page { margin:0; size:A4 landscape; } }
"""

    cover = (
        '<div class="cover">'
        '<h1>Behavior Report</h1>'
        f'<div class="sub">Currency: <strong style="color:white">{currency}</strong></div>'
        f'<div class="sub">Period: <strong style="color:white">{period}</strong></div>'
        f'<div class="meta">Generated: {generated} &nbsp;·&nbsp; Vantage Circle · Internal</div>'
        '</div>'
    )
    footer = f'<div class="footer">Behavior Report · {currency} · {period} · {generated}</div>'

    return (
        '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        f'<title>Behavior Report — {currency}</title>'
        f'<style>{css}</style></head><body>'
        + cover + lag_section + cohort_section + trend_section + footer
        + '</body></html>'
    )
