import pandas as pd
import streamlit as st

CURRENCY_SYMBOLS = {
    "INR": "₹", "USD": "$", "AED": "AED ", "SGD": "S$",
    "GBP": "£", "EUR": "€", "MYR": "RM ", "PHP": "₱", "BDT": "৳",
    "CAD": "CA$",
}


def fmt_amount(amount, currency):
    sym = CURRENCY_SYMBOLS.get(currency, currency + " ")
    if currency == "INR":
        if amount >= 1e7:
            return f"{sym}{amount / 1e7:.1f}Cr"
        if amount >= 1e5:
            return f"{sym}{amount / 1e5:.1f}L"
        if amount >= 1e3:
            return f"{sym}{amount / 1e3:.1f}K"
        return f"{sym}{amount:.0f}"
    else:
        if amount >= 1e6:
            return f"{sym}{amount / 1e6:.1f}M"
        if amount >= 1e3:
            return f"{sym}{amount / 1e3:.1f}K"
        return f"{sym}{amount:.0f}"


@st.cache_data
def kpis(df: pd.DataFrame) -> dict:
    total = len(df)
    activated = df["is_activated"].sum()
    breakage_rows = df[df["is_breakage"]]
    breakage_count = len(breakage_rows)
    breakage_amount = breakage_rows["Amount"].sum()
    total_amount = df["Amount"].sum()
    activated_amount = df[df["is_activated"]]["Amount"].sum()
    return {
        "total": total,
        "activated": int(activated),
        "activation_rate": round(activated / total * 100, 2) if total else 0,
        "breakage_count": breakage_count,
        "breakage_amount": round(breakage_amount, 2),
        "breakage_pct": round(breakage_amount / total_amount * 100, 2) if total_amount else 0,
        "total_amount": round(total_amount, 2),
        "activated_amount": round(activated_amount, 2),
    }


def activated_amount_for_currency(df: pd.DataFrame, currency: str) -> float:
    return round(df[(df["Currency"] == currency) & df["is_activated"]]["Amount"].sum(), 2)


@st.cache_data
def maturity_threshold_days(df: pd.DataFrame, pct: float = 0.95) -> int:
    """
    How many days after redemption until `pct` of all activations have occurred,
    derived from cohorts old enough to be fully settled (redeemed 180+ days ago).
    Falls back to 60 if there is not enough historical data.
    """
    max_date = df["Redemption Date"].max()
    settled_cutoff = max_date - pd.Timedelta(days=180)
    settled = df[df["Redemption Date"] < settled_cutoff]
    activated = settled[settled["is_activated"] & settled["activation_lag_days"].notna()]

    if len(activated) < 20:
        return 60

    return max(1, int(activated["activation_lag_days"].quantile(pct)))


@st.cache_data
def preliminary_months(df: pd.DataFrame) -> tuple:
    """
    Returns (frozenset of month-strings that are preliminary, threshold_days).
    Preliminary = redeemed within maturity_threshold_days of the latest date in df.
    """
    threshold = maturity_threshold_days(df)
    max_date = df["Redemption Date"].max()
    cutoff_period = pd.Period(max_date - pd.Timedelta(days=threshold), "M")
    prelim = frozenset(
        str(m) for m in df["redemption_month"].dropna().unique() if m > cutoff_period
    )
    return prelim, threshold


@st.cache_data
def monthly_trend_v2(df: pd.DataFrame) -> pd.DataFrame:
    breakage_df = df[df["is_breakage"]]
    g = df.groupby("redemption_month")
    bg = breakage_df.groupby("redemption_month")

    result = pd.DataFrame({
        "total": g.size(),
        "activated": g["is_activated"].sum(),
        "breakage_count": bg.size(),
        "breakage_amount": bg["Amount"].sum(),
    }).fillna(0)
    result.index.name = "redemption_month"
    result = result.reset_index()
    result["redemption_month"] = result["redemption_month"].astype(str)
    result["not_activated"] = (result["total"] - result["activated"]).astype(int)
    result["activated"] = result["activated"].astype(int)
    result["breakage_count"] = result["breakage_count"].astype(int)
    result["breakage_amount"] = result["breakage_amount"].round(2)
    result["activation_rate"] = (
        result["activated"] / result["total"].replace(0, float("nan")) * 100
    ).round(2).fillna(0)
    return result


@st.cache_data
def weekly_trend(df: pd.DataFrame, currency: str = "") -> pd.DataFrame:
    from modules.holidays import get_holiday_weeks
    df_copy = df[df["Redemption Date"].notna()].copy()
    df_copy["week_start"] = (
        df_copy["Redemption Date"].dt.to_period("W-MON").dt.start_time.dt.date
    )
    breakage_df = df_copy[df_copy["is_breakage"]]
    g = df_copy.groupby("week_start")
    bg = breakage_df.groupby("week_start")

    result = pd.DataFrame({
        "total": g.size(),
        "breakage_count": bg.size(),
        "breakage_amount": bg["Amount"].sum(),
    }).fillna(0)
    result.index.name = "week_start"
    result = result.reset_index()
    result["week_label"] = result["week_start"].apply(lambda d: pd.Timestamp(d).strftime("%b %d"))
    result["breakage_count"] = result["breakage_count"].astype(int)
    result["breakage_amount"] = result["breakage_amount"].round(2)
    result["breakage_rate"] = (
        result["breakage_count"] / result["total"].replace(0, float("nan")) * 100
    ).round(2).fillna(0)
    holiday_map = get_holiday_weeks(result["week_start"].tolist(), currency)
    result["holiday_label"] = result["week_start"].map(lambda d: holiday_map.get(d, ""))
    return result.sort_values("week_start").reset_index(drop=True)


_DOW_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

@st.cache_data
def breakage_by_dow(df: pd.DataFrame) -> pd.DataFrame:
    """Breakage rate and volume grouped by redemption day-of-week (Mon=0 … Sun=6)."""
    valid = df[df["Redemption Date"].notna()].copy()
    if valid.empty:
        return pd.DataFrame()
    valid["dow"] = valid["Redemption Date"].dt.dayofweek
    g = valid.groupby("dow")
    bg = valid[valid["is_breakage"]].groupby("dow")
    result = pd.DataFrame({
        "total": g.size(),
        "breakage_count": bg.size(),
    }).reindex(range(7), fill_value=0)
    result.index.name = "dow"
    result = result.reset_index()
    result["breakage_rate"] = (
        result["breakage_count"] / result["total"].replace(0, float("nan")) * 100
    ).round(2).fillna(0)
    result["day_label"] = result["dow"].map(lambda d: _DOW_LABELS[d])
    return result


_DENOM_BINS = {
    # Currency: (bins, labels)
    "INR": ([0, 500, 1000, 5000, float("inf")], ["<₹500", "₹500–1k", "₹1k–5k", "₹5k+"]),
    "USD": ([0, 10, 50, 100, 500, float("inf")], ["<$10", "$10–50", "$50–100", "$100–500", "$500+"]),
    "CAD": ([0, 10, 50, 100, 500, float("inf")], ["<CA$10", "CA$10–50", "CA$50–100", "CA$100–500", "CA$500+"]),
    "GBP": ([0, 10, 50, 100, 500, float("inf")], ["<£10", "£10–50", "£50–100", "£100–500", "£500+"]),
    "EUR": ([0, 10, 50, 100, 500, float("inf")], ["<€10", "€10–50", "€50–100", "€100–500", "€500+"]),
    "AED": ([0, 50, 200, 500, float("inf")], ["<AED 50", "AED 50–200", "AED 200–500", "AED 500+"]),
    "SGD": ([0, 10, 50, 100, 500, float("inf")], ["<S$10", "S$10–50", "S$50–100", "S$100–500", "S$500+"]),
    "MYR": ([0, 50, 200, 500, float("inf")], ["<RM 50", "RM 50–200", "RM 200–500", "RM 500+"]),
    "PHP": ([0, 500, 2000, 5000, float("inf")], ["<₱500", "₱500–2k", "₱2k–5k", "₱5k+"]),
    "BDT": ([0, 500, 2000, 5000, float("inf")], ["<৳500", "৳500–2k", "৳2k–5k", "৳5k+"]),
}
_DENOM_DEFAULT = ([0, 10, 50, 100, 500, float("inf")], ["<10", "10–50", "50–100", "100–500", "500+"])


@st.cache_data
def breakage_by_denomination(df: pd.DataFrame, currency: str = None) -> pd.DataFrame:
    if currency is None:
        currencies = df["Currency"].dropna().unique()
        currency = currencies[0] if len(currencies) == 1 else None
    bins, labels = _DENOM_BINS.get(currency, _DENOM_DEFAULT) if currency else _DENOM_DEFAULT
    d = df.copy()
    d["denomination_bucket"] = pd.cut(d["Amount"], bins=bins, labels=labels, right=True)

    g = d.groupby("denomination_bucket", observed=True)
    bg = d[d["is_breakage"]].groupby("denomination_bucket", observed=True)

    total = g.agg(total_count=("Amount", "count"))
    breakage = bg.agg(breakage_count=("Amount", "count"), breakage_amount=("Amount", "sum"))

    result = total.join(breakage, how="left").fillna(0).reset_index()
    result.rename(columns={"denomination_bucket": "denomination"}, inplace=True)
    result["denomination"] = result["denomination"].astype(str)
    result["breakage_count"] = result["breakage_count"].astype(int)
    result["breakage_amount"] = result["breakage_amount"].round(2)
    result["breakage_rate"] = (
        result["breakage_count"] / result["total_count"].replace(0, float("nan")) * 100
    ).round(2).fillna(0)
    return result


@st.cache_data
def breakage_by_card_type(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("card_type")
    bg = df[df["is_breakage"]].groupby("card_type")

    total = g.agg(total_count=("Amount", "count"), total_amount=("Amount", "sum"))
    breakage = bg.agg(breakage_count=("Amount", "count"), breakage_amount=("Amount", "sum"))

    result = total.join(breakage, how="left").fillna(0).reset_index()
    result["breakage_count"] = result["breakage_count"].astype(int)
    result["breakage_amount"] = result["breakage_amount"].round(2)
    result["total_amount"] = result["total_amount"].round(2)
    result["breakage_rate"] = (
        result["breakage_count"] / result["total_count"].replace(0, float("nan")) * 100
    ).round(2).fillna(0)
    result["breakage_amount_pct"] = (
        result["breakage_amount"] / result["total_amount"].replace(0, float("nan")) * 100
    ).round(2).fillna(0)
    return result


@st.cache_data
def breakage_by_brand(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("Brand")
    bg = df[df["is_breakage"]].groupby("Brand")

    total = g.agg(total_count=("Amount", "count"), total_amount=("Amount", "sum"))
    breakage = bg.agg(breakage_count=("Amount", "count"), breakage_amount=("Amount", "sum"))

    result = total.join(breakage, how="left").fillna(0).reset_index()
    result.rename(columns={"Brand": "brand"}, inplace=True)
    result["breakage_count"] = result["breakage_count"].astype(int)
    result["breakage_amount"] = result["breakage_amount"].round(2)
    result["total_amount"] = result["total_amount"].round(2)
    result["breakage_rate"] = (
        result["breakage_count"] / result["total_count"].replace(0, float("nan")) * 100
    ).round(2).fillna(0)
    return result.sort_values("breakage_amount", ascending=False)


@st.cache_data
def breakage_by_company(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("Company")
    bg = df[df["is_breakage"]].groupby("Company")

    total = g.agg(total_count=("Amount", "count"), total_amount=("Amount", "sum"))
    breakage = bg.agg(breakage_count=("Amount", "count"), breakage_amount=("Amount", "sum"))

    result = total.join(breakage, how="left").fillna(0).reset_index()
    result.rename(columns={"Company": "company"}, inplace=True)
    result["breakage_count"] = result["breakage_count"].astype(int)
    result["breakage_amount"] = result["breakage_amount"].round(2)
    result["total_amount"] = result["total_amount"].round(2)
    result["breakage_rate"] = (
        result["breakage_count"] / result["total_count"].replace(0, float("nan")) * 100
    ).round(2).fillna(0)
    return result.sort_values("breakage_amount", ascending=False)


@st.cache_data
def breakage_by_geography(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("Country")
    bg = df[df["is_breakage"]].groupby("Country")

    total = g.agg(total_count=("Amount", "count"), total_amount=("Amount", "sum"))
    breakage = bg.agg(breakage_count=("Amount", "count"), breakage_amount=("Amount", "sum"))

    result = total.join(breakage, how="left").fillna(0).reset_index()
    result.rename(columns={"Country": "country"}, inplace=True)
    result["breakage_count"] = result["breakage_count"].astype(int)
    result["breakage_amount"] = result["breakage_amount"].round(2)
    result["total_amount"] = result["total_amount"].round(2)
    result["breakage_rate"] = (
        result["breakage_count"] / result["total_count"].replace(0, float("nan")) * 100
    ).round(2).fillna(0)
    return result.sort_values("breakage_amount", ascending=False)


@st.cache_data
def cohort_table(df: pd.DataFrame) -> pd.DataFrame:
    windows = [7, 30, 90, 180]
    rows = []
    for month, group in df.groupby("redemption_month"):
        total = len(group)
        row = {"Redemption Month": str(month), "Total": total}
        for w in windows:
            count = (group["activation_lag_days"] <= w).sum()
            row[f"≤{w}d"] = f"{round(count / total * 100, 1)}%" if total else "—"
        never = group["is_breakage"].sum()
        row["Never"] = f"{round(never / total * 100, 1)}%" if total else "—"
        rows.append(row)
    return pd.DataFrame(rows)


@st.cache_data
def cohort_survival(df: pd.DataFrame, currency: str) -> pd.DataFrame:
    """For each cohort, % of cards still unactivated at each day threshold."""
    df_c = df[df["Currency"] == currency]
    thresholds = [1, 7, 14, 30, 60, 90, 180]
    rows = []
    for month, group in df_c.groupby("redemption_month"):
        total = len(group)
        if total < 5:
            continue
        not_yet = (~group["is_activated"]).sum()
        row = {"cohort": str(month)}
        for t in thresholds:
            activated_late = (group["is_activated"] & (group["activation_lag_days"] > t)).sum()
            row[f"day_{t}"] = round((not_yet + activated_late) / total * 100, 1)
        rows.append(row)
    return pd.DataFrame(rows)


@st.cache_data
def activation_heatmap_data(df: pd.DataFrame) -> pd.DataFrame:
    """7×24 pivot of activation counts by day-of-week × hour."""
    activated = df[df["is_activated"] & df["Activation Date"].notna()].copy()
    if activated.empty:
        return pd.DataFrame()
    activated["dow"] = activated["Activation Date"].dt.dayofweek
    activated["hour"] = activated["Activation Date"].dt.hour
    counts = activated.groupby(["dow", "hour"]).size().reset_index(name="count")
    pivot = counts.pivot(index="dow", columns="hour", values="count").fillna(0)
    for h in range(24):
        if h not in pivot.columns:
            pivot[h] = 0
    for d in range(7):
        if d not in pivot.index:
            pivot.loc[d] = 0
    return pivot.sort_index()[sorted(pivot.columns)]


@st.cache_data
def cohort_activation_matrix(df: pd.DataFrame, currency: str):
    df_c = df[df["Currency"] == currency]
    if df_c.empty:
        return None

    r_months = sorted(df_c["redemption_month"].dropna().unique())
    a_months = sorted(df_c["activation_month"].dropna().unique())
    if not r_months:
        return None

    max_date = df_c["Redemption Date"].max()
    threshold = maturity_threshold_days(df_c)
    open_boundary = pd.Period(max_date - pd.Timedelta(days=threshold), "M")
    open_cohorts = {m for m in r_months if m > open_boundary}

    # Pre-build aggregates to avoid O(n) DataFrame filters in inner loop
    totals = df_c.groupby("redemption_month").size()

    act_df = df_c[df_c["is_activated"] & df_c["activation_month"].notna()]
    if not act_df.empty:
        count_pivot = (
            act_df.groupby(["redemption_month", "activation_month"])
            .size()
            .unstack(fill_value=0)
            .reindex(index=r_months, columns=a_months, fill_value=0)
        )
        amount_pivot = (
            act_df.groupby(["redemption_month", "activation_month"])["Amount"]
            .sum()
            .unstack(fill_value=0)
            .reindex(index=r_months, columns=a_months, fill_value=0)
        )
    else:
        count_pivot = pd.DataFrame(0, index=r_months, columns=a_months)
        amount_pivot = pd.DataFrame(0.0, index=r_months, columns=a_months)

    never_g = df_c[df_c["is_breakage"]].groupby("redemption_month")
    never_counts = never_g.size().reindex(r_months, fill_value=0)
    never_amounts = never_g["Amount"].sum().reindex(r_months, fill_value=0)

    act_z, act_pct_text, act_amount_text = [], [], []
    never_z, never_pct_text, never_amount_text = [], [], []

    for r_month in r_months:
        total = totals.get(r_month, 0)
        z_row, pct_row, amt_row = [], [], []
        for a_month in a_months:
            if a_month < r_month:
                z_row.append(None)
                pct_row.append("")
                amt_row.append("")
            else:
                count = count_pivot.loc[r_month, a_month] if a_month in count_pivot.columns else 0
                amount = amount_pivot.loc[r_month, a_month] if a_month in amount_pivot.columns else 0
                pct = count / total * 100 if total else 0
                if count > 0:
                    z_row.append(pct)
                    pct_row.append(f"{pct:.1f}%")
                    amt_row.append(fmt_amount(amount, currency))
                else:
                    z_row.append(None)
                    pct_row.append("")
                    amt_row.append("")
        act_z.append(z_row)
        act_pct_text.append(pct_row)
        act_amount_text.append(amt_row)

        n_count = int(never_counts.get(r_month, 0))
        n_amount = never_amounts.get(r_month, 0)
        n_pct = n_count / total * 100 if total else 0
        prefix = "~" if r_month in open_cohorts else ""
        never_z.append([n_pct])
        never_pct_text.append([f"{prefix}{n_pct:.1f}%"])
        never_amount_text.append([f"{prefix}{fmt_amount(n_amount, currency)}"])

    return {
        "act_z": act_z,
        "act_pct_text": act_pct_text,
        "act_amount_text": act_amount_text,
        "never_z": never_z,
        "never_pct_text": never_pct_text,
        "never_amount_text": never_amount_text,
        "row_labels": [str(m) for m in r_months],
        "act_cols": [str(m) for m in a_months],
        "open_cohorts": {str(m) for m in open_cohorts},
        "currency": currency,
    }


@st.cache_data
def kpi_deltas(trend_df: pd.DataFrame, prelim_months: frozenset = None) -> dict:
    """Compare most recent mature month vs the one before it."""
    prelim_months = prelim_months or frozenset()
    mature = trend_df[~trend_df["redemption_month"].isin(prelim_months)]

    if len(mature) < 2:
        mature = trend_df

    if len(mature) < 2:
        curr = mature.iloc[-1] if len(mature) == 1 else None
        return {
            "breakage_rate": (100 - curr["activation_rate"]) if curr is not None else 0,
            "breakage_rate_delta": None,
            "breakage_amount": curr["breakage_amount"] if curr is not None else 0,
            "breakage_amount_delta": None,
        }
    curr = mature.iloc[-1]
    prev = mature.iloc[-2]
    curr_br = 100 - curr["activation_rate"]
    prev_br = 100 - prev["activation_rate"]
    return {
        "breakage_rate": round(curr_br, 2),
        "breakage_rate_delta": round(curr_br - prev_br, 2),
        "breakage_amount": curr["breakage_amount"],
        "breakage_amount_delta": round(curr["breakage_amount"] - prev["breakage_amount"], 2),
        "current_month": curr["redemption_month"],
        "prev_month": prev["redemption_month"],
    }


@st.cache_data
def generate_insights(df: pd.DataFrame, currency: str) -> list:
    """Short insight bullets for Overview page. Uses mature cohorts for rate comparisons."""
    df_c = df[df["Currency"] == currency]
    if df_c.empty:
        return []

    prelim, threshold_days = preliminary_months(df_c)
    mature_df = df_c[~df_c["redemption_month"].astype(str).isin(prelim)]
    base_df = mature_df if len(mature_df) >= 20 else df_c

    insights = []

    if prelim:
        insights.append(
            f"⚠️ {len(prelim)} recent month(s) are preliminary (within the {threshold_days}-day "
            f"activation window) and are excluded from trend analysis below."
        )

    ct = breakage_by_card_type(base_df)
    if len(ct) >= 2:
        closed = ct[ct["card_type"] == "closed_loop"]
        open_ = ct[ct["card_type"] == "open_loop"]
        if not closed.empty and not open_.empty:
            cr = closed.iloc[0]["breakage_rate"]
            or_ = open_.iloc[0]["breakage_rate"]
            higher = "Closed-loop" if cr > or_ else "Open-loop"
            lower = "open-loop" if cr > or_ else "closed-loop"
            insights.append(
                f"{higher} cards have a {max(cr, or_):.1f}% breakage rate vs "
                f"{min(cr, or_):.1f}% for {lower} — a {abs(cr - or_):.1f}pp difference."
            )

    denom = breakage_by_denomination(base_df, currency=currency)
    if not denom.empty and denom["breakage_rate"].max() > 0:
        top = denom.loc[denom["breakage_rate"].idxmax()]
        insights.append(
            f"Cards in the {top['denomination']} range have the highest non-activation rate "
            f"at {top['breakage_rate']:.1f}%."
        )

    activated = df_c[df_c["is_activated"] & df_c["activation_lag_days"].notna()]
    if len(activated) > 10:
        within_7d = (activated["activation_lag_days"] <= 7).sum()
        pct_quick = within_7d / len(activated) * 100
        insights.append(
            f"{pct_quick:.0f}% of activations happen within the first 7 days — "
            f"cards not activated by day 7 are very likely to become breakage."
        )

    company_df = breakage_by_company(base_df)
    if not company_df.empty and len(company_df) >= 2:
        avg_rate = company_df["breakage_rate"].mean()
        top = company_df.iloc[0]
        if top["breakage_rate"] > avg_rate * 1.5:
            insights.append(
                f"{top['company']} has a {top['breakage_rate']:.1f}% breakage rate — "
                f"{top['breakage_rate'] - avg_rate:.1f}pp above average."
            )

    return insights


@st.cache_data
def generate_full_insights(df: pd.DataFrame, currency: str) -> dict:
    df_c = df[df["Currency"] == currency]
    if df_c.empty:
        return {}

    k = kpis(df_c)
    trend = monthly_trend_v2(df_c)
    prelim, threshold_days = preliminary_months(df_c)
    mature_trend = trend[~trend["redemption_month"].isin(prelim)]
    breakage_rate = round(100 - k["activation_rate"], 2)

    out = {
        "summary": "", "this_month": [], "trends": [],
        "client_alerts": [], "drivers": [], "forecast": "",
        "preliminary_months": sorted(prelim),
        "threshold_days": threshold_days,
    }

    if breakage_rate < 5:
        health = "healthy — most cards are being activated"
    elif breakage_rate < 15:
        health = "moderate — there is room to improve activation"
    else:
        health = "elevated — a significant share of cards are going unactivated"

    if len(mature_trend) > 0:
        mature_k = kpis(df_c[~df_c["redemption_month"].astype(str).isin(prelim)])
        mature_br = round(100 - mature_k["activation_rate"], 2)
        mature_note = (
            f" (calculated on {len(mature_trend)} mature cohort(s); "
            f"{len(prelim)} recent month(s) excluded as still within the {threshold_days}-day activation window)"
        )
    else:
        mature_br = breakage_rate
        mature_note = ""

    out["summary"] = (
        f"Mature-cohort breakage rate is {mature_br}% ({health}){mature_note}. "
        f"Total confirmed breakage: {fmt_amount(k['breakage_amount'], currency)} across "
        f"{k['breakage_count']:,} cards ({k['total']:,} total redemptions). "
        f"{fmt_amount(k['activated_amount'], currency)} has been successfully activated by employees."
    )

    if len(mature_trend) > 0:
        latest = mature_trend.iloc[-1]
        latest_br = round(100 - latest["activation_rate"], 2)
        out["this_month"].append(
            f"Latest settled cohort ({latest['redemption_month']}): breakage rate of {latest_br:.1f}% "
            f"— {latest['breakage_count']:,} cards, {fmt_amount(latest['breakage_amount'], currency)}."
        )

    if len(prelim) > 0:
        prelim_list = ", ".join(sorted(prelim))
        out["this_month"].append(
            f"⚠️ {len(prelim)} recent month(s) ({prelim_list}) are within the {threshold_days}-day "
            f"activation window and are marked preliminary — their breakage rates will fall as more "
            f"employees activate their cards."
        )

    if len(mature_trend) >= 2:
        latest = mature_trend.iloc[-1]
        prev = mature_trend.iloc[-2]
        latest_br = round(100 - latest["activation_rate"], 2)
        prev_br = round(100 - prev["activation_rate"], 2)
        delta = round(latest_br - prev_br, 1)
        if abs(delta) >= 0.5:
            direction = "increased" if delta > 0 else "decreased"
            out["this_month"].append(
                f"Breakage rate {direction} by {abs(delta):.1f}pp vs {prev['redemption_month']} ({prev_br:.1f}%) — "
                f"comparison uses settled cohorts only."
            )
        else:
            out["this_month"].append(
                f"Breakage rate stable vs {prev['redemption_month']} ({prev_br:.1f}% → {latest_br:.1f}%) — "
                f"settled cohorts only."
            )

    if len(mature_trend) >= 3:
        rates = (100 - mature_trend["activation_rate"]).round(2).tolist()
        first_r, last_r = rates[0], rates[-1]
        first_m = mature_trend.iloc[0]["redemption_month"]
        last_m = mature_trend.iloc[-1]["redemption_month"]

        if last_r > first_r + 2:
            out["trends"].append(
                f"Breakage rate is trending upward across settled cohorts — "
                f"{first_r:.1f}% ({first_m}) → {last_r:.1f}% ({last_m}). This warrants attention."
            )
        elif last_r < first_r - 2:
            out["trends"].append(
                f"Breakage rate has improved across settled cohorts — "
                f"{first_r:.1f}% ({first_m}) → {last_r:.1f}% ({last_m})."
            )
        else:
            out["trends"].append(
                f"Breakage rate has been relatively stable across settled cohorts, "
                f"ranging from {min(rates):.1f}% to {max(rates):.1f}%."
            )

        avg_r = sum(rates) / len(rates)
        peak_idx = rates.index(max(rates))
        peak_m = mature_trend.iloc[peak_idx]["redemption_month"]
        out["trends"].append(
            f"Average breakage rate (settled cohorts): {avg_r:.1f}%. "
            f"Peak settled month: {peak_m} at {max(rates):.1f}%."
        )

    activated_df = df_c[df_c["is_activated"] & df_c["activation_lag_days"].notna()]
    if len(activated_df) >= 10:
        within_7d = (activated_df["activation_lag_days"] <= 7).mean() * 100
        within_1d = (activated_df["activation_lag_days"] <= 1).mean() * 100
        median_lag = activated_df["activation_lag_days"].median()
        out["trends"].append(
            f"{within_7d:.0f}% of activations occur within the first 7 days "
            f"({within_1d:.0f}% within 24 hours). Median time to activate: {median_lag:.0f} days. "
            f"Cards not activated by day 7 are very unlikely to ever be activated."
        )

    company_df = breakage_by_company(df_c)
    if not company_df.empty and len(company_df) >= 2:
        avg_br = company_df["breakage_rate"].mean()
        high = company_df[company_df["breakage_rate"] > avg_br * 1.5]
        for _, row in high.head(3).iterrows():
            out["client_alerts"].append(
                f"{row['company']} has a breakage rate of {row['breakage_rate']:.1f}% — "
                f"{row['breakage_rate'] - avg_br:.1f}pp above the {avg_br:.1f}% average. "
                f"Breakage: {fmt_amount(row['breakage_amount'], currency)} ({row['breakage_count']:,} cards)."
            )
        if k["breakage_amount"] > 0:
            top = company_df.iloc[0]
            out["client_alerts"].append(
                f"{top['company']} accounts for {fmt_amount(top['breakage_amount'], currency)} "
                f"({top['breakage_amount'] / k['breakage_amount'] * 100:.0f}% of total breakage)."
            )

    denom = breakage_by_denomination(df_c, currency=currency)
    if not denom.empty and denom["breakage_rate"].max() > 0:
        top_rate = denom.loc[denom["breakage_rate"].idxmax()]
        top_amt = denom.loc[denom["breakage_amount"].idxmax()]
        out["drivers"].append(
            f"The {top_rate['denomination']} denomination bucket has the highest non-activation rate "
            f"at {top_rate['breakage_rate']:.1f}%. "
            f"The {top_amt['denomination']} bucket contributes the most breakage value: "
            f"{fmt_amount(top_amt['breakage_amount'], currency)}."
        )

    ct = breakage_by_card_type(df_c)
    if len(ct) >= 2:
        closed = ct[ct["card_type"] == "closed_loop"]
        open_ = ct[ct["card_type"] == "open_loop"]
        if not closed.empty and not open_.empty:
            cr = closed.iloc[0]["breakage_rate"]
            or_ = open_.iloc[0]["breakage_rate"]
            higher = "Closed-loop" if cr > or_ else "Open-loop"
            lower = "open-loop" if cr > or_ else "closed-loop"
            out["drivers"].append(
                f"{higher} cards have a {max(cr, or_):.1f}% breakage rate vs {min(cr, or_):.1f}% for {lower} "
                f"— a {abs(cr - or_):.1f}pp gap."
            )

    if len(trend) >= 3:
        latest_months = trend.tail(2)["redemption_month"].tolist()
        open_cohort = df_c[df_c["redemption_month"].astype(str).isin(latest_months) & ~df_c["is_activated"]]
        if len(open_cohort) > 0:
            mature = trend.iloc[:-2]
            if mature["total"].sum() > 0:
                avg_act_pct = mature["activated"].sum() / mature["total"].sum()
            else:
                avg_act_pct = k["activation_rate"] / 100
            expected_breakage = int(len(open_cohort) * (1 - avg_act_pct))
            avg_breakage_card = df_c[df_c["is_breakage"]]["Amount"].mean() if k["breakage_count"] > 0 else 0
            projected = round(expected_breakage * avg_breakage_card, 0)
            out["forecast"] = (
                f"There are {len(open_cohort):,} unactivated cards from recent months still within window. "
                f"Based on historical patterns ({avg_act_pct * 100:.0f}% eventual activation rate), "
                f"approximately {expected_breakage:,} are expected to remain unactivated — "
                f"projecting an additional {fmt_amount(projected, currency)} in breakage revenue."
            )

    return out


# ── Micro trend functions ─────────────────────────────────────────────────────

def card_type_trends(df: pd.DataFrame) -> pd.DataFrame:
    """Monthly card type composition and breakage rate. Returns tidy long-format df."""
    tmp = df.copy()
    tmp["month"] = tmp["redemption_month"].astype(str)
    grouped = (
        tmp.groupby(["month", "card_type"])
        .agg(count=("Reference ID", "count"), breakage=("is_breakage", "sum"))
        .reset_index()
    )
    monthly_total = grouped.groupby("month")["count"].transform("sum")
    grouped["share_pct"] = (grouped["count"] / monthly_total * 100).round(1)
    grouped["breakage_rate"] = (grouped["breakage"] / grouped["count"] * 100).round(1)
    return grouped.sort_values(["month", "card_type"]).reset_index(drop=True)


def brand_shift_trends(df: pd.DataFrame, recent_n: int = 3, prior_n: int = 3) -> pd.DataFrame:
    """Compare brand share % between recent N months vs prior N months.
    Returns df with columns: Brand, card_type, recent_share, prior_share, delta."""
    sorted_months = sorted(df["redemption_month"].unique())
    if len(sorted_months) < recent_n + 1:
        return pd.DataFrame()
    recent_months = sorted_months[-recent_n:]
    prior_months  = sorted_months[-(recent_n + prior_n):-recent_n]
    if not prior_months:
        return pd.DataFrame()

    recent_df = df[df["redemption_month"].isin(recent_months)]
    prior_df  = df[df["redemption_month"].isin(prior_months)]

    def share(frame):
        total = len(frame)
        if total == 0:
            return pd.Series(dtype=float)
        return frame.groupby("Brand")["Reference ID"].count() / total * 100

    recent_share = share(recent_df).rename("recent_share")
    prior_share  = share(prior_df).rename("prior_share")
    ctype        = df.groupby("Brand")["card_type"].first()

    result = (
        pd.concat([recent_share, prior_share, ctype], axis=1)
        .fillna(0)
    )
    result["delta"] = (result["recent_share"] - result["prior_share"]).round(2)
    result = result[result["recent_share"] > 0.05].reset_index()
    result.columns = ["Brand", "recent_share", "prior_share", "card_type", "delta"]
    return result.sort_values("delta", ascending=False).reset_index(drop=True)
