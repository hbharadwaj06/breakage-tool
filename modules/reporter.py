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
