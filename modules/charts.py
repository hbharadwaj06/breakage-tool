import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Design-system-aligned chart palette
_PALETTE = [
    "#5b3b97",  # brand-500 purple
    "#ff6d05",  # accent orange
    "#a086d0",  # brand-300 lavender
    "#0ba5ec",  # info blue
    "#12b76a",  # success green
    "#f79009",  # warning amber
    "#f04438",  # error red
    "#475467",  # neutral-600
    "#7a56bd",  # brand-400
]


def _fmt_month(m_str: str) -> str:
    try:
        p = pd.Period(m_str, "M")
        return p.to_timestamp().strftime("%b '%y")
    except Exception:
        return m_str


def monthly_bar(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_bar(x=df["redemption_month"], y=df["total"], name="Total Redeemed", marker_color=_PALETTE[1])
    fig.add_bar(x=df["redemption_month"], y=df["activated"], name="Activated", marker_color=_PALETTE[0])
    fig.update_layout(
        barmode="group",
        xaxis_title="Redemption Month",
        yaxis_title="Count",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=40),
    )
    return fig


def activation_rate_line(df: pd.DataFrame, overall_rate: float) -> go.Figure:
    fig = go.Figure()
    fig.add_scatter(
        x=df["redemption_month"], y=df["activation_rate"],
        mode="lines+markers", name="Activation Rate %",
        line=dict(color=_PALETTE[0], width=2), marker=dict(size=6),
    )
    fig.add_hline(y=overall_rate, line_dash="dash", line_color="grey",
                  annotation_text=f"Overall {overall_rate}%", annotation_position="bottom right")
    fig.update_layout(xaxis_title="Redemption Month", yaxis_title="Activation Rate %",
                      yaxis=dict(range=[0, 105]), margin=dict(t=40))
    return fig


def denomination_bar(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_bar(x=df["denomination"], y=df["breakage_amount"], name="Breakage Amount",
                marker_color=_PALETTE[3], text=df["breakage_rate"].map(lambda v: f"{v}%"), textposition="outside")
    fig.update_layout(xaxis_title="Denomination Bucket", yaxis_title="Breakage Amount", margin=dict(t=40))
    return fig


def denomination_count_bar(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_bar(x=df["denomination"], y=df["breakage_count"], name="Breakage Count",
                marker_color=_PALETTE[4], text=df["breakage_rate"].map(lambda v: f"{v}%"), textposition="outside")
    fig.update_layout(xaxis_title="Denomination Bucket", yaxis_title="Breakage Count", margin=dict(t=40))
    return fig


def card_type_donut(df: pd.DataFrame) -> go.Figure:
    fig = px.pie(df, names="card_type", values="breakage_amount", hole=0.55, color_discrete_sequence=_PALETTE)
    fig.update_traces(textinfo="percent+label")
    fig.update_layout(margin=dict(t=40, b=20))
    return fig


def brand_bar(df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    subset = df.head(top_n)
    fig = go.Figure(go.Bar(
        x=subset["breakage_amount"], y=subset["brand"], orientation="h",
        marker_color=_PALETTE[2], text=subset["breakage_rate"].map(lambda v: f"{v}%"), textposition="outside",
    ))
    fig.update_layout(xaxis_title="Breakage Amount", yaxis=dict(autorange="reversed"), margin=dict(t=40, l=10))
    return fig


def company_breakage_chart(df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    subset = df.head(top_n)
    fig = go.Figure(go.Bar(
        x=subset["breakage_amount"], y=subset["company"], orientation="h",
        marker_color="#c0392b", text=subset["breakage_rate"].map(lambda v: f"{v}%"), textposition="outside",
    ))
    fig.update_layout(
        xaxis_title="Breakage Amount", yaxis=dict(autorange="reversed"),
        margin=dict(t=20, l=10, r=80, b=40), plot_bgcolor="white", paper_bgcolor="white",
    )
    fig.update_xaxes(showgrid=False)
    return fig


def geography_treemap(df: pd.DataFrame) -> go.Figure:
    fig = px.treemap(df, path=["country"], values="breakage_amount", color="breakage_rate",
                     color_continuous_scale="RdYlGn_r", hover_data=["total_count", "breakage_count"])
    fig.update_layout(margin=dict(t=40))
    return fig


def lag_histogram(df: pd.DataFrame) -> go.Figure:
    activated = df[df["is_activated"] & df["activation_lag_days"].notna()]
    fig = px.histogram(activated, x="activation_lag_days", nbins=40,
                       color_discrete_sequence=[_PALETTE[0]], labels={"activation_lag_days": "Days to Activate"})
    fig.update_layout(xaxis_title="Days between Redemption and Activation", yaxis_title="Count",
                      margin=dict(t=40), plot_bgcolor="white", paper_bgcolor="white")
    return fig


def survival_curve_chart(survival_df: pd.DataFrame) -> go.Figure:
    cols = [c for c in survival_df.columns if c.startswith("day_")]
    days = [int(c.split("_")[1]) for c in cols]
    colors = px.colors.qualitative.Plotly

    fig = go.Figure()
    for i, (_, row) in enumerate(survival_df.iterrows()):
        y_vals = [row[c] for c in cols]
        fig.add_trace(go.Scatter(
            x=days, y=y_vals, mode="lines+markers",
            name=_fmt_month(row["cohort"]),
            line=dict(color=colors[i % len(colors)], width=2),
            marker=dict(size=5),
            hovertemplate=f"Cohort {_fmt_month(row['cohort'])}<br>Day %{{x}}: %{{y:.1f}}% unactivated<extra></extra>",
        ))

    fig.update_layout(
        xaxis_title="Days since redemption",
        yaxis_title="% Still Unactivated",
        yaxis=dict(range=[0, 105]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=60, b=50, l=60, r=20),
        plot_bgcolor="white", paper_bgcolor="white",
    )
    fig.update_xaxes(showgrid=False, tickvals=days)
    fig.update_yaxes(gridcolor="#f0f0f0")
    return fig


def activation_timing_heatmap(pivot_df: pd.DataFrame) -> go.Figure:
    dow_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    hours = list(range(24))
    hour_labels = [f"{h:02d}:00" for h in hours]

    z = []
    for d in range(7):
        if d in pivot_df.index:
            row_vals = [int(pivot_df.loc[d, h]) if h in pivot_df.columns else 0 for h in hours]
        else:
            row_vals = [0] * 24
        z.append(row_vals)

    fig = go.Figure(go.Heatmap(
        z=z, x=hour_labels, y=dow_labels,
        colorscale=[[0, "#ffffff"], [0.3, "#c6efce"], [0.7, "#4CAF50"], [1.0, "#008000"]],
        showscale=True, colorbar=dict(title="Activations"),
        hovertemplate="Day: %{y}<br>Hour: %{x}<br>Activations: %{z}<extra></extra>",
    ))
    fig.update_layout(
        xaxis_title="Hour of Day", yaxis=dict(autorange="reversed"),
        margin=dict(t=20, b=60, l=80, r=20), plot_bgcolor="white", paper_bgcolor="white",
    )
    return fig


def weekly_trend_chart(weekly_df: pd.DataFrame) -> go.Figure:
    avg = weekly_df["breakage_rate"].mean()
    holiday_col = "holiday_label" if "holiday_label" in weekly_df.columns else None
    has_holidays = holiday_col and weekly_df[holiday_col].any()

    # Per-bar colors keep all bars in chronological order
    colors = (
        weekly_df[holiday_col].map(lambda h: "#e67e22" if h else "#c0392b").tolist()
        if has_holidays
        else ["#c0392b"] * len(weekly_df)
    )
    customdata = [
        f"{r['week_label']}: {r['breakage_rate']:.1f}%<br>🗓 {r[holiday_col]}"
        if has_holidays and r[holiday_col]
        else f"{r['week_label']}: {r['breakage_rate']:.1f}%"
        for _, r in weekly_df.iterrows()
    ]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=weekly_df["week_label"],
        y=weekly_df["breakage_rate"],
        marker_color=colors,
        customdata=customdata,
        hovertemplate="%{customdata}<extra></extra>",
        showlegend=False,
    ))

    if has_holidays:
        # Dummy invisible traces just for the legend
        for label, color in [("Normal week", "#c0392b"), ("Holiday / festival week", "#e67e22")]:
            fig.add_trace(go.Scatter(
                x=[None], y=[None], mode="markers",
                marker=dict(color=color, size=10, symbol="square"),
                name=label, showlegend=True,
            ))

    fig.add_hline(y=avg, line_dash="dash", line_color="#999",
                  annotation_text=f"Avg {avg:.1f}%", annotation_position="bottom right",
                  annotation_font_color="#555")
    fig.update_layout(
        xaxis_title=None, yaxis_title="Breakage Rate %",
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0,
                    font_size=11) if has_holidays else dict(visible=False),
        margin=dict(t=30 if has_holidays else 10, b=80, l=60, r=20),
        plot_bgcolor="white", paper_bgcolor="white",
    )
    fig.update_xaxes(showgrid=False, tickangle=45)
    fig.update_yaxes(gridcolor="#f0f0f0")
    return fig


def dow_breakage_chart(dow_df: pd.DataFrame) -> go.Figure:
    """Bar chart of breakage rate by day of week, with volume as a secondary line."""
    avg = dow_df["breakage_rate"].mean()
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=dow_df["day_label"],
        y=dow_df["breakage_rate"],
        name="Breakage rate",
        marker_color="#c0392b",
        yaxis="y1",
        customdata=list(zip(dow_df["breakage_rate"], dow_df["total"])),
        hovertemplate="%{x}: %{customdata[0]:.1f}%  (%{customdata[1]:,} cards)<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=dow_df["day_label"],
        y=dow_df["total"],
        name="Cards redeemed",
        mode="lines+markers",
        line=dict(color="#7f8c8d", width=2, dash="dot"),
        marker=dict(size=5),
        yaxis="y2",
        hovertemplate="%{x}: %{y:,} cards<extra></extra>",
    ))

    fig.add_hline(y=avg, line_dash="dash", line_color="#bbb",
                  annotation_text=f"Avg {avg:.1f}%", annotation_position="bottom right",
                  annotation_font_color="#555", yref="y1")

    fig.update_layout(
        xaxis_title=None,
        yaxis=dict(title="Breakage Rate %", showgrid=True, gridcolor="#f0f0f0"),
        yaxis2=dict(title="Cards redeemed", overlaying="y", side="right",
                    showgrid=False, tickformat=","),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0, font_size=11),
        margin=dict(t=30, b=40, l=60, r=60),
        plot_bgcolor="white", paper_bgcolor="white",
        bargap=0.3,
    )
    fig.update_xaxes(showgrid=False)
    return fig


def pending_pipeline_bar(pdf: pd.DataFrame, mode: str = "count", currency: str = "") -> go.Figure:
    """Stacked bar per redemption month: Activated vs Still-Pending, with the
    pending slice coloured by cohort maturity. mode: 'count' or 'amount'."""
    months = [_fmt_month(m) for m in pdf["redemption_month"]]
    in_window = pdf["status"] == "In-window"

    if mode == "amount":
        from modules.calculator import fmt_amount
        activated = pdf["activated_amount"]
        pending = pdf["pending_amount"]
        y_title = f"Amount ({currency})" if currency else "Amount"
        val_fmt = (lambda v: fmt_amount(v, currency)) if currency else (lambda v: f"{v:,.0f}")
    else:
        activated = pdf["activated"].astype(float)
        pending = pdf["pending_count"].astype(float)
        y_title = "Card Count"
        val_fmt = lambda v: f"{v:,.0f}"

    pending_open = [p if w else 0 for p, w in zip(pending, in_window)]
    pending_lost = [p if not w else 0 for p, w in zip(pending, in_window)]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=months, y=activated, name="Activated",
        marker_color="#12b76a",
        hovertemplate="%{x}<br>Activated: %{text}<extra></extra>",
        text=[val_fmt(v) for v in activated], textposition="none",
    ))
    fig.add_trace(go.Bar(
        x=months, y=pending_open, name="Pending — in window (may convert)",
        marker_color="#f79009",
        hovertemplate="%{x}<br>Pending (in window): %{text}<extra></extra>",
        text=[val_fmt(v) for v in pending_open], textposition="none",
    ))
    fig.add_trace(go.Bar(
        x=months, y=pending_lost, name="Pending — matured (lost)",
        marker_color="#f04438",
        hovertemplate="%{x}<br>Pending (matured): %{text}<extra></extra>",
        text=[val_fmt(v) for v in pending_lost], textposition="none",
    ))

    fig.update_layout(
        barmode="stack",
        xaxis_title=None, yaxis_title=y_title,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font_size=11),
        margin=dict(t=40, b=40, l=70, r=20),
        plot_bgcolor="white", paper_bgcolor="white",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#f0f0f0")
    return fig


def cohort_heatmap(matrix_data: dict, mode: str = "cards") -> go.Figure:
    """Redemption month × activation month heatmap.

    mode:
      'cards'  → % of cards (colour + label)          [legacy alias: 'pct']
      'value'  → % of currency value (colour + label)
      'amount' → currency amount label, coloured by % of value
    """
    row_labels = [_fmt_month(m) for m in matrix_data["row_labels"]]
    act_labels = [_fmt_month(m) for m in matrix_data["act_cols"]]

    if mode in ("cards", "pct"):
        act_z, never_z = matrix_data["act_z"], matrix_data["never_z"]
        act_text, never_text = matrix_data["act_pct_text"], matrix_data["never_pct_text"]
    elif mode == "value":
        act_z, never_z = matrix_data["act_amt_z"], matrix_data["never_amt_z"]
        act_text, never_text = matrix_data["act_amt_pct_text"], matrix_data["never_amt_pct_text"]
    else:  # amount — currency labels, coloured by share of value
        act_z, never_z = matrix_data["act_amt_z"], matrix_data["never_amt_z"]
        act_text, never_text = matrix_data["act_amount_text"], matrix_data["never_amount_text"]

    _GREEN = [[0.0, "rgb(237,247,239)"], [0.15, "rgb(198,239,206)"],
              [0.5, "rgb(99,190,123)"], [1.0, "rgb(0,128,43)"]]
    _RED = [[0.0, "rgb(253,242,242)"], [0.15, "rgb(255,199,206)"],
            [0.5, "rgb(220,80,80)"], [1.0, "rgb(156,0,6)"]]

    # Two shared-axis panels: activation matrix (left) + tight Never column
    # (right). Splitting them removes the dead space that appeared when a lone
    # "Never" category was stretched across a single wide axis.
    from plotly.subplots import make_subplots
    fig = make_subplots(
        rows=1, cols=2,
        column_widths=[0.9, 0.1] if act_labels else [0.001, 0.999],
        horizontal_spacing=0.03,
        shared_yaxes=True,
    )

    _AXIS = dict(color="#475467", tickfont=dict(size=11), fixedrange=True)

    if act_labels:
        fig.add_trace(go.Heatmap(
            x=act_labels, y=row_labels, z=act_z,
            text=act_text, texttemplate="%{text}", textfont=dict(size=11),
            colorscale=_GREEN, zmin=0, zmax=100, showscale=False,
            xgap=3, ygap=3, hoverongaps=False,
            hovertemplate="Redeemed %{y} · activated %{x}<br><b>%{text}</b><extra></extra>",
        ), row=1, col=1)

    fig.add_trace(go.Heatmap(
        x=["Never"], y=row_labels, z=never_z,
        text=never_text, texttemplate="%{text}", textfont=dict(size=11),
        colorscale=_RED, zmin=0, zmax=100, showscale=False,
        xgap=3, ygap=3, hoverongaps=False,
        hovertemplate="Redeemed %{y} · never activated<br><b>%{text}</b><extra></extra>",
    ), row=1, col=2)

    n_rows = len(row_labels)
    fig.update_layout(
        height=max(300, n_rows * 52 + 110),
        margin=dict(t=20, b=60, l=90, r=16),
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(color="#475467"),
    )
    fig.update_yaxes(autorange="reversed", showgrid=False, ticks="", zeroline=False,
                     title_text="Redemption Month", **_AXIS, row=1, col=1)
    fig.update_yaxes(autorange="reversed", showgrid=False, ticks="", zeroline=False,
                     **_AXIS, row=1, col=2)
    fig.update_xaxes(showgrid=False, ticks="", side="bottom",
                     title_text="Activation Month", **_AXIS, row=1, col=1)
    fig.update_xaxes(showgrid=False, ticks="", **_AXIS, row=1, col=2)
    return fig


def breakage_trend_exec(trend_df: pd.DataFrame, prelim_months: frozenset = None) -> go.Figure:
    """Area chart of breakage rate. Shades preliminary (right-censored) months in grey."""
    df = trend_df.copy()
    df["breakage_rate"] = (100 - df["activation_rate"]).round(2)
    months = [_fmt_month(m) for m in df["redemption_month"]]
    prelim_months = prelim_months or frozenset()

    mature_rates = [
        r for m, r in zip(df["redemption_month"], df["breakage_rate"])
        if str(m) not in prelim_months
    ]
    avg = (sum(mature_rates) / len(mature_rates)) if mature_rates else df["breakage_rate"].mean()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=months, y=df["breakage_rate"], mode="lines+markers",
        fill="tozeroy", fillcolor="rgba(0,128,43,0.12)",
        line=dict(color="#008000", width=2.5), marker=dict(size=7, color="#008000"),
        hovertemplate="%{x}: %{y:.1f}%<extra></extra>",
    ))
    fig.add_hline(y=avg, line_dash="dash", line_color="#999",
                  annotation_text=f"Avg {avg:.1f}% (settled)", annotation_position="bottom right",
                  annotation_font_color="#555")

    # Shade preliminary months
    if prelim_months:
        prelim_formatted = [_fmt_month(m) for m in sorted(prelim_months)]
        prelim_in_chart = [m for m in prelim_formatted if m in months]
        if prelim_in_chart:
            first_prelim = prelim_in_chart[0]
            fig.add_vrect(
                x0=first_prelim, x1=months[-1],
                fillcolor="rgba(180,180,180,0.18)",
                line_width=0,
                annotation_text="Preliminary",
                annotation_position="top left",
                annotation_font_color="#999",
                annotation_font_size=11,
            )

    fig.update_layout(
        xaxis_title=None,
        yaxis=dict(title="Breakage Rate %", range=[0, min(100, df["breakage_rate"].max() * 1.3 + 5)]),
        showlegend=False, margin=dict(t=20, b=40, l=60, r=20),
        plot_bgcolor="white", paper_bgcolor="white",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#f0f0f0")
    return fig


# ── Micro trend charts ────────────────────────────────────────────────────────

_CARD_TYPE_COLORS = {
    "amazon":     "#f79009",
    "closed_loop": "#5b3b97",
    "open_loop":  "#0ba5ec",
}

_CARD_TYPE_LABELS = {
    "amazon":     "Amazon",
    "closed_loop": "Closed Loop",
    "open_loop":  "Open Loop (Mastercard)",
}


def card_type_composition_chart(trends_df: pd.DataFrame) -> go.Figure:
    """Stacked bar: % share of each card type per month."""
    fig = go.Figure()
    for ctype in ["amazon", "closed_loop", "open_loop"]:
        sub = trends_df[trends_df["card_type"] == ctype]
        if sub.empty:
            continue
        fig.add_trace(go.Bar(
            x=sub["month"],
            y=sub["share_pct"],
            name=_CARD_TYPE_LABELS.get(ctype, ctype),
            marker_color=_CARD_TYPE_COLORS.get(ctype, "#999"),
            hovertemplate="%{x}<br>Share: %{y:.1f}%<extra>" + _CARD_TYPE_LABELS.get(ctype, ctype) + "</extra>",
        ))
    fig.update_layout(
        barmode="stack",
        xaxis_title=None, yaxis_title="Share %",
        yaxis=dict(range=[0, 100], ticksuffix="%"),
        legend=dict(orientation="h", y=-0.15),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(t=20, b=60, l=60, r=20),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#f0f0f0")
    return fig


def card_type_breakage_chart(trends_df: pd.DataFrame) -> go.Figure:
    """Line chart: breakage rate per card type over time."""
    fig = go.Figure()
    for ctype in ["amazon", "closed_loop", "open_loop"]:
        sub = trends_df[trends_df["card_type"] == ctype]
        if sub.empty or len(sub) < 2:
            continue
        fig.add_trace(go.Scatter(
            x=sub["month"], y=sub["breakage_rate"],
            name=_CARD_TYPE_LABELS.get(ctype, ctype),
            mode="lines+markers",
            line=dict(color=_CARD_TYPE_COLORS.get(ctype, "#999"), width=2),
            marker=dict(size=6),
            hovertemplate="%{x}<br>Breakage: %{y:.1f}%<extra>" + _CARD_TYPE_LABELS.get(ctype, ctype) + "</extra>",
        ))
    fig.update_layout(
        xaxis_title=None, yaxis_title="Breakage Rate %",
        yaxis=dict(ticksuffix="%"),
        legend=dict(orientation="h", y=-0.15),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(t=20, b=60, l=60, r=20),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#f0f0f0")
    return fig


def brand_shift_chart(shift_df: pd.DataFrame, top_n: int = 12) -> go.Figure:
    """Horizontal bar: brand share delta (recent 3M vs prior 3M)."""
    if shift_df.empty:
        return go.Figure()

    gainers = shift_df.nlargest(top_n // 2, "delta")
    losers  = shift_df.nsmallest(top_n // 2, "delta")
    plot_df = pd.concat([gainers, losers]).drop_duplicates("Brand").sort_values("delta")

    colors = ["#f04438" if d < 0 else "#12b76a" for d in plot_df["delta"]]

    fig = go.Figure(go.Bar(
        x=plot_df["delta"],
        y=plot_df["Brand"],
        orientation="h",
        marker_color=colors,
        hovertemplate="%{y}<br>Δ share: %{x:+.2f}pp<extra></extra>",
    ))
    fig.add_vline(x=0, line_color="#ccc", line_width=1)
    fig.update_layout(
        xaxis_title="Share change (percentage points)",
        yaxis_title=None,
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(t=20, b=40, l=200, r=40),
        height=max(300, len(plot_df) * 30),
    )
    fig.update_xaxes(gridcolor="#f0f0f0", zeroline=False)
    fig.update_yaxes(showgrid=False)
    return fig
