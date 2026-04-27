import json
import os
import pandas as pd

REQUIRED_COLUMNS = [
    "Reference ID", "Deal ID", "Brand", "User_ID", "Company",
    "Country", "Currency", "Amount", "Points",
    "Redemption Status", "Redemption Date", "Activation Date",
    "Final Redemption Status",
]

BRAND_TYPES_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "brand_types.json")
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def load_brand_types() -> dict:
    with open(BRAND_TYPES_PATH) as f:
        return json.load(f)


# ── Persistent store helpers ──────────────────────────────────────────────────

def get_stored_files() -> list:
    os.makedirs(DATA_DIR, exist_ok=True)
    return sorted([f for f in os.listdir(DATA_DIR) if f.lower().endswith(".csv")])


def save_uploaded_file(uploaded_file) -> str:
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, uploaded_file.name)
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return path


def delete_stored_file(filename: str):
    path = os.path.join(DATA_DIR, filename)
    if os.path.exists(path):
        os.remove(path)


def load_from_store() -> tuple:
    """Load and merge all CSVs in data/. Returns (df, warnings)."""
    stored = get_stored_files()
    if not stored:
        return None, []
    paths = [os.path.join(DATA_DIR, f) for f in stored]
    return _load_paths(paths)


# ── Core load / merge ─────────────────────────────────────────────────────────

def load_csvs(uploaded_files) -> tuple:
    frames = []
    warnings = []

    for uf in uploaded_files:
        try:
            raw = pd.read_csv(uf)
        except Exception as e:
            warnings.append(f"{uf.name}: failed to parse — {e}")
            continue

        missing = [c for c in REQUIRED_COLUMNS if c not in raw.columns]
        if missing:
            warnings.append(f"{uf.name}: missing columns {missing} — skipped")
            continue

        raw["_source_file"] = uf.name
        frames.append(raw[REQUIRED_COLUMNS + ["_source_file"]])

    if not frames:
        return None, warnings

    merged = pd.concat(frames, ignore_index=True)
    merged = _clean(merged)
    merged, dup_count = _dedup(merged)

    if dup_count:
        warnings.append(f"Removed {dup_count} duplicate rows (matched on Reference ID + User_ID + Brand).")

    return merged, warnings


def _load_paths(paths: list) -> tuple:
    frames = []
    warnings = []

    for path in paths:
        name = os.path.basename(path)
        try:
            raw = pd.read_csv(path)
        except Exception as e:
            warnings.append(f"{name}: failed to parse — {e}")
            continue

        missing = [c for c in REQUIRED_COLUMNS if c not in raw.columns]
        if missing:
            warnings.append(f"{name}: missing columns {missing} — skipped")
            continue

        raw["_source_file"] = name
        frames.append(raw[REQUIRED_COLUMNS + ["_source_file"]])

    if not frames:
        return None, warnings

    merged = pd.concat(frames, ignore_index=True)
    merged = _clean(merged)
    merged, dup_count = _dedup(merged)

    if dup_count:
        warnings.append(f"Removed {dup_count} duplicate rows across all stored files.")

    return merged, warnings


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    df["Redemption Date"] = pd.to_datetime(df["Redemption Date"], errors="coerce")
    df["Activation Date"] = pd.to_datetime(df["Activation Date"], errors="coerce")
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)
    df["Points"] = pd.to_numeric(df["Points"], errors="coerce").fillna(0)
    df["Reference ID"] = df["Reference ID"].astype(str).str.strip()
    df["User_ID"] = df["User_ID"].astype(str).str.strip()
    df["Brand"] = df["Brand"].astype(str).str.strip()

    # Final Redemption Status: 1 = activated, 0 = not activated
    df["Final Redemption Status"] = pd.to_numeric(
        df["Final Redemption Status"], errors="coerce"
    ).fillna(0).astype(int)

    brand_types = load_brand_types()
    # brand_types keys are substrings (case-insensitive) — e.g. "Visa" matches "Visa* CAD Gift Card"
    def _map_card_type(brand: str) -> str:
        brand_lower = brand.lower()
        for key, ctype in brand_types.items():
            if key.lower() in brand_lower:
                return ctype
        return "closed_loop"
    df["card_type"] = df["Brand"].apply(_map_card_type)
    df["composite_key"] = df["Reference ID"] + "|" + df["User_ID"] + "|" + df["Brand"]

    df["is_activated"] = df["Final Redemption Status"] == 1
    df["is_breakage"] = df["Final Redemption Status"] == 0
    df["activation_lag_days"] = (df["Activation Date"] - df["Redemption Date"]).dt.days
    df["redemption_month"] = df["Redemption Date"].dt.to_period("M")
    df["activation_month"] = df["Activation Date"].dt.to_period("M")

    return df


def _dedup(df: pd.DataFrame) -> tuple:
    before = len(df)
    # Activated records (1) take priority over unactivated (0) for the same card
    df = df.sort_values("Final Redemption Status", ascending=False)
    df = df.drop_duplicates(subset=["composite_key"], keep="first")
    return df.reset_index(drop=True), before - len(df)


def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    if filters.get("date_range"):
        start, end = filters["date_range"]
        start_p = pd.Period(start, "M")
        end_p = pd.Period(end, "M")
        df = df[df["redemption_month"].between(start_p, end_p)]

    if filters.get("countries"):
        df = df[df["Country"].isin(filters["countries"])]

    if filters.get("companies"):
        df = df[df["Company"].isin(filters["companies"])]

    if filters.get("currencies"):
        df = df[df["Currency"].isin(filters["currencies"])]

    return df
