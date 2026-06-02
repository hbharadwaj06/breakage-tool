import datetime
import functools
import io
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
DATA_DIR    = os.path.join(os.path.dirname(__file__), "..", "data")
RAW_DIR     = os.path.join(DATA_DIR, "raw")
STORE_PATH  = os.path.join(DATA_DIR, "store.parquet")
SNAP_DIR    = os.path.join(DATA_DIR, "snapshots")
MAX_SNAPSHOTS = 10


@functools.lru_cache(maxsize=1)
def load_brand_types() -> dict:
    with open(BRAND_TYPES_PATH) as f:
        return json.load(f)


def ensure_loaded() -> None:
    """Call at the top of any page that needs data.
    - If df is already in session state: does nothing.
    - If store exists: auto-loads with a spinner, then reruns so the page renders with data.
    - If no store at all: shows a welcome screen with a button to go upload data.
    """
    import streamlit as st

    if "df" in st.session_state:
        return

    has_store = os.path.exists(STORE_PATH)
    has_raw   = os.path.exists(RAW_DIR) and any(
        f.endswith(".csv.gz") for f in os.listdir(RAW_DIR)
    ) if os.path.exists(RAW_DIR) else False

    if has_store or has_raw:
        with st.spinner("Loading data…"):
            df, warnings = load_from_store()
        for w in warnings:
            st.warning(w)
        if df is not None:
            st.session_state["df"] = df
            st.rerun()
        else:
            st.error("Could not load data store. Go to Upload → Rebuild Store.")
            st.stop()
    else:
        # No data at all — show welcome screen
        st.markdown("<br><br>", unsafe_allow_html=True)
        col_l, col_m, col_r = st.columns([1, 2, 1])
        with col_m:
            st.markdown("## Welcome to Breakage Analysis")
            st.markdown(
                "No data has been loaded yet. Upload your monthly CSV files to get started."
            )
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Go to Upload page", type="primary", use_container_width=True):
                st.switch_page("pages/1_Upload.py")
        st.stop()


# ── Remote backend (Supabase / OneDrive) ─────────────────────────────────────

def _remote_backend():
    from modules import gdrive, onedrive
    if gdrive.is_configured():
        return gdrive
    if onedrive.is_configured():
        return onedrive
    return None


# ── Local store helpers ───────────────────────────────────────────────────────

def get_stored_files() -> list:
    """Return list of source file names (without .gz) available in raw/ or remote."""
    backend = _remote_backend()
    if backend:
        return backend.list_csv_files()
    os.makedirs(RAW_DIR, exist_ok=True)
    return sorted(
        f.replace(".csv.gz", ".csv")
        for f in os.listdir(RAW_DIR)
        if f.lower().endswith(".csv.gz")
    )


def save_uploaded_file(uploaded_file) -> None:
    backend = _remote_backend()
    if backend:
        backend.upload_csv(uploaded_file.name, bytes(uploaded_file.getbuffer()))
        return

    os.makedirs(RAW_DIR, exist_ok=True)

    # Validate columns before saving
    try:
        preview = pd.read_csv(io.BytesIO(uploaded_file.getbuffer()), nrows=5)
    except Exception as e:
        raise ValueError(f"Cannot parse CSV: {e}")
    missing = [c for c in REQUIRED_COLUMNS if c not in preview.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    gz_name = uploaded_file.name.replace(".csv", "") + ".csv.gz"
    path = os.path.join(RAW_DIR, gz_name)
    content = bytes(uploaded_file.getbuffer())
    df = pd.read_csv(io.BytesIO(content), low_memory=False)
    df[REQUIRED_COLUMNS].to_csv(path, index=False, compression="gzip")

    rebuild_store()


def delete_stored_file(filename: str) -> None:
    backend = _remote_backend()
    if backend:
        backend.delete_csv(filename)
        return

    gz_name = filename.replace(".csv", "") + ".csv.gz"
    path = os.path.join(RAW_DIR, gz_name)
    if os.path.exists(path):
        os.remove(path)
    rebuild_store()


def rebuild_store() -> tuple:
    """Re-read all raw CSVs, dedup, save store.parquet + a dated snapshot.
    Returns (row_count, warnings)."""
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(SNAP_DIR, exist_ok=True)

    frames, warnings = [], []
    for fname in sorted(os.listdir(RAW_DIR)):
        if not fname.lower().endswith(".csv.gz"):
            continue
        path = os.path.join(RAW_DIR, fname)
        try:
            df = pd.read_csv(path, low_memory=False, compression="gzip")
        except Exception as e:
            warnings.append(f"{fname}: failed to read — {e}")
            continue
        missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            warnings.append(f"{fname}: missing columns {missing} — skipped")
            continue
        df = df[REQUIRED_COLUMNS].copy()
        df["_source_file"] = fname.replace(".csv.gz", ".csv")
        frames.append(df)

    if not frames:
        if os.path.exists(STORE_PATH):
            os.remove(STORE_PATH)
        return 0, warnings

    merged = pd.concat(frames, ignore_index=True)
    merged["Final Redemption Status"] = pd.to_numeric(
        merged["Final Redemption Status"], errors="coerce"
    ).fillna(0).astype(int)
    merged["composite_key"] = (
        merged["Reference ID"].astype(str).str.strip() + "|" +
        merged["User_ID"].astype(str).str.strip() + "|" +
        merged["Brand"].astype(str).str.strip()
    )
    before = len(merged)
    merged = merged.sort_values("Final Redemption Status", ascending=False)
    merged = merged.drop_duplicates(subset=["composite_key"], keep="first")
    merged = merged.drop(columns=["composite_key"]).reset_index(drop=True)
    dup_count = before - len(merged)
    if dup_count:
        warnings.append(f"Removed {dup_count:,} duplicate rows during rebuild.")

    merged.to_parquet(STORE_PATH, index=False, compression="snappy")

    # Save dated snapshot and prune old ones
    today = datetime.date.today().isoformat()
    snap_path = os.path.join(SNAP_DIR, f"store_{today}.parquet")
    merged.to_parquet(snap_path, index=False, compression="snappy")
    _prune_snapshots()

    return len(merged), warnings


def restore_snapshot(snapshot_filename: str) -> None:
    """Copy a snapshot over store.parquet to roll back to that date."""
    src = os.path.join(SNAP_DIR, snapshot_filename)
    if not os.path.exists(src):
        raise FileNotFoundError(f"Snapshot not found: {snapshot_filename}")
    import shutil
    shutil.copy2(src, STORE_PATH)


def list_snapshots() -> list:
    """Return snapshot filenames sorted newest-first."""
    if not os.path.exists(SNAP_DIR):
        return []
    return sorted(
        [f for f in os.listdir(SNAP_DIR) if f.endswith(".parquet")],
        reverse=True,
    )


def _prune_snapshots():
    snaps = list_snapshots()
    for old in snaps[MAX_SNAPSHOTS:]:
        os.remove(os.path.join(SNAP_DIR, old))


# ── Load from store ───────────────────────────────────────────────────────────

def load_from_store() -> tuple:
    """Load from remote backend or local store.parquet. Returns (df, warnings)."""
    backend = _remote_backend()
    if backend:
        files = backend.list_csv_files()
        if not files:
            return None, []
        frames, warnings = [], []
        for name in files:
            try:
                raw = pd.read_csv(io.BytesIO(backend.download_csv(name)))
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

    # Local: use store.parquet if available, else rebuild
    if not os.path.exists(STORE_PATH):
        raw_files = [f for f in os.listdir(RAW_DIR) if f.endswith(".csv.gz")] if os.path.exists(RAW_DIR) else []
        if not raw_files:
            return None, []
        rebuild_store()

    try:
        df = pd.read_parquet(STORE_PATH)
    except Exception as e:
        return None, [f"store.parquet is corrupted ({e}). Use 'Rebuild Store' to recover."]

    df = _clean(df)
    return df, []


# ── Core load / merge (for preview of uploaded files before saving) ───────────

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


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Redemption Date"] = pd.to_datetime(df["Redemption Date"], errors="coerce")
    df["Activation Date"] = pd.to_datetime(df["Activation Date"], errors="coerce")
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)
    df["Points"] = pd.to_numeric(df["Points"], errors="coerce").fillna(0)
    df["Reference ID"] = df["Reference ID"].astype(str).str.strip()
    df["User_ID"] = df["User_ID"].astype(str).str.strip()
    df["Brand"] = df["Brand"].astype(str).str.strip()

    df["Final Redemption Status"] = pd.to_numeric(
        df["Final Redemption Status"], errors="coerce"
    ).fillna(0).astype(int)

    brand_types = load_brand_types()
    df["card_type"] = "closed_loop"
    brand_lower = df["Brand"].str.lower()
    for key, ctype in reversed(list(brand_types.items())):
        df.loc[brand_lower.str.contains(key.lower(), regex=False, na=False), "card_type"] = ctype

    df["composite_key"] = df["Reference ID"] + "|" + df["User_ID"] + "|" + df["Brand"]
    df["is_activated"] = df["Final Redemption Status"] == 1
    df["is_breakage"] = df["Final Redemption Status"] == 0
    df["activation_lag_days"] = (df["Activation Date"] - df["Redemption Date"]).dt.days
    df["redemption_month"] = df["Redemption Date"].dt.to_period("M")
    df["activation_month"] = df["Activation Date"].dt.to_period("M")

    return df


def _dedup(df: pd.DataFrame) -> tuple:
    before = len(df)
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
