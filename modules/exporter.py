import io
import pandas as pd
from modules import calculator


def build_excel(df: pd.DataFrame) -> bytes:
    """Return a multi-sheet Excel workbook as bytes."""
    buf = io.BytesIO()

    monthly = calculator.monthly_trend_v2(df)
    by_brand = calculator.breakage_by_brand(df)
    dominant_currency = df["Currency"].mode().iloc[0] if not df.empty else None
    by_denom = calculator.breakage_by_denomination(df, currency=dominant_currency)
    by_geo = calculator.breakage_by_geography(df)
    cohort = calculator.cohort_table(df)
    by_card = calculator.breakage_by_card_type(df)

    export_raw = df.drop(columns=["composite_key", "redemption_month", "activation_month"], errors="ignore").copy()
    for col in ["is_activated", "is_breakage"]:
        if col in export_raw.columns:
            export_raw[col] = export_raw[col].map({True: "Yes", False: "No"})

    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        export_raw.to_excel(writer, sheet_name="Raw Data", index=False)
        monthly.to_excel(writer, sheet_name="Monthly Summary", index=False)
        by_brand.to_excel(writer, sheet_name="By Brand", index=False)
        by_denom.to_excel(writer, sheet_name="By Denomination", index=False)
        by_geo.to_excel(writer, sheet_name="By Country", index=False)
        by_card.to_excel(writer, sheet_name="By Card Type", index=False)
        cohort.to_excel(writer, sheet_name="Cohort Table", index=False)

    return buf.getvalue()
