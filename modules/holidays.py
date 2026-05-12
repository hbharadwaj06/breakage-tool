from datetime import date, timedelta

try:
    import holidays as _hol
    _HOLIDAYS_AVAILABLE = True
except ImportError:
    _HOLIDAYS_AVAILABLE = False

# Best-effort mapping: ISO currency → ISO 3166-1 alpha-2 country code
_CURRENCY_TO_COUNTRY = {
    "INR": "IN",
    "USD": "US",
    "GBP": "GB",
    "SGD": "SG",
    "AED": "AE",
    "EUR": "DE",
    "CAD": "CA",
    "AUD": "AU",
    "JPY": "JP",
    "PHP": "PH",
    "MYR": "MY",
    "THB": "TH",
    "IDR": "ID",
    "SAR": "SA",
    "ZAR": "ZA",
    "BRL": "BR",
    "MXN": "MX",
    "NGN": "NG",
    "KES": "KE",
    "QAR": "QA",
    "BHD": "BH",
    "KWD": "KW",
    "OMR": "OM",
    "NZD": "NZ",
    "HKD": "HK",
    "CNY": "CN",
}


def get_holiday_weeks(week_starts: list, currency: str) -> dict:
    """
    Returns {week_start_date: "Holiday Name, ..."} for weeks containing a public holiday.
    week_starts: list of date/Timestamp objects (Monday of each week).
    currency: ISO 4217 currency code.
    """
    if not _HOLIDAYS_AVAILABLE or not week_starts:
        return {}

    country = _CURRENCY_TO_COUNTRY.get(currency.upper() if currency else "")
    if not country:
        return {}

    # Collect all calendar years spanned by the weeks
    years = set()
    for ws in week_starts:
        d = ws if isinstance(ws, date) else ws.date() if hasattr(ws, "date") else ws
        years.add(d.year)
        years.add((d + timedelta(days=6)).year)

    try:
        h = _hol.country_holidays(country, years=list(years), language="en_US")
    except Exception:
        try:
            h = _hol.country_holidays(country, years=list(years))
        except Exception:
            return {}

    result = {}
    for ws in week_starts:
        ws_date = ws if isinstance(ws, date) else ws.date() if hasattr(ws, "date") else ws
        names = []
        for i in range(7):
            day = ws_date + timedelta(days=i)
            if day in h:
                name = h[day]
                if name not in names:
                    names.append(name)
        if names:
            result[ws_date] = ", ".join(names)

    return result
