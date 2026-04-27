import requests
import streamlit as st
from datetime import date

_API_URL = "https://open.er-api.com/v6/latest/USD"


def fetch_rates() -> tuple:
    """Fetch USD-based exchange rates from free API. Returns (rates_dict, error_str|None)."""
    cache_key = f"_fx_rates_{date.today()}"
    if cache_key in st.session_state:
        return st.session_state[cache_key], None
    try:
        r = requests.get(_API_URL, timeout=6)
        data = r.json()
        if data.get("result") == "success":
            rates = data["rates"]  # {"USD": 1.0, "INR": 83.5, "CAD": 1.36, ...}
            st.session_state[cache_key] = rates
            return rates, None
        return {}, "Exchange rate API returned an unexpected response."
    except Exception as e:
        return {}, f"Could not fetch rates ({e}). Enter rates manually below."


def convert_to(amount: float, from_currency: str, to_currency: str, rates: dict):
    """Convert amount → to_currency. Returns None if rate missing."""
    if not rates:
        return None
    if from_currency == to_currency:
        return amount
    if from_currency not in rates or to_currency not in rates:
        return None
    return (amount / rates[from_currency]) * rates[to_currency]


def consolidate(df, to_currency: str, rates: dict) -> list:
    """
    For each currency in df, compute total and breakage amounts, then convert to to_currency.
    Returns list of dicts sorted by converted_breakage desc.
    """
    rows = []
    for currency, grp in df.groupby("Currency"):
        orig_total    = grp["Amount"].sum()
        orig_breakage = grp[grp["is_breakage"]]["Amount"].sum()
        conv_total    = convert_to(orig_total,    currency, to_currency, rates)
        conv_breakage = convert_to(orig_breakage, currency, to_currency, rates)
        rows.append({
            "currency":         currency,
            "orig_total":       orig_total,
            "orig_breakage":    orig_breakage,
            "conv_total":       conv_total,
            "conv_breakage":    conv_breakage,
            "convertible":      conv_breakage is not None,
        })
    rows.sort(key=lambda r: r["conv_breakage"] or 0, reverse=True)
    return rows
