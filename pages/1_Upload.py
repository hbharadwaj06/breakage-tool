import os
import streamlit as st
from modules.loader import (
    load_csvs, get_stored_files, save_uploaded_file, delete_stored_file,
    load_from_store, rebuild_store, list_snapshots, restore_snapshot,
    RAW_DIR, STORE_PATH, SNAP_DIR,
)
from modules.auth import require_login, is_admin
from modules.ui import apply_theme, page_header

require_login()
apply_theme()
if not is_admin():
    st.error("Access denied. Only administrators can upload data.")
    st.stop()

page_header("Upload Data", "Add new monthly CSV files · Admin only")
st.markdown("---")


# ── Stored files ──────────────────────────────────────────────────────────────
st.subheader("Stored Data Files")
stored = get_stored_files()

if stored:
    store_mb = os.path.getsize(STORE_PATH) / 1024 / 1024 if os.path.exists(STORE_PATH) else 0
    raw_mb = sum(
        os.path.getsize(os.path.join(RAW_DIR, f + ".gz"))
        for f in stored
        if os.path.exists(os.path.join(RAW_DIR, f + ".gz"))
    ) / 1024 / 1024
    st.markdown(
        f"**{len(stored)} source file(s)** · "
        f"Raw (compressed): **{raw_mb:.1f} MB** · "
        f"Active store: **{store_mb:.1f} MB**"
    )
    for fname in stored:
        c1, c2 = st.columns([8, 1])
        c1.markdown(f"📄 `{fname}`")
        if c2.button("Delete", key=f"del_{fname}"):
            delete_stored_file(fname)
            if "df" in st.session_state:
                del st.session_state["df"]
            st.rerun()
else:
    st.info("No files stored yet. Upload below to get started.")

st.markdown("---")


# ── Upload new files ──────────────────────────────────────────────────────────
st.subheader("Upload New Files")
st.markdown(
    "Upload the **latest month's CSV(s)** only — they are added to existing data. "
    "Previously uploaded months are preserved automatically."
)
st.markdown(
    "**Two types of uploads are handled automatically:**\n"
    "- New records (fresh redemptions) → added as new rows\n"
    "- Status updates (cards that were unactivated and are now activated) → "
    "the activated version replaces the old one, same card is never double-counted"
)

uploaded = st.file_uploader("Select one or more CSV files", type="csv", accept_multiple_files=True)

if uploaded:
    saved, errors = [], []
    for uf in uploaded:
        try:
            save_uploaded_file(uf)
            saved.append(uf.name)
        except ValueError as e:
            errors.append(f"**{uf.name}**: {e}")
    if saved:
        st.success(f"Saved and store rebuilt: {', '.join(saved)}")
    for err in errors:
        st.error(err)
    if "df" in st.session_state:
        del st.session_state["df"]
    st.rerun()

st.markdown("---")


# ── Recovery tools ────────────────────────────────────────────────────────────
st.subheader("Recovery Tools")

col_rebuild, col_snap = st.columns(2)

with col_rebuild:
    st.markdown("**Rebuild Store**")
    st.caption("Re-reads all source files and rebuilds the active store from scratch. Use if data looks wrong.")
    if st.button("Rebuild Store from Source Files", use_container_width=True):
        with st.spinner("Rebuilding..."):
            count, warnings = rebuild_store()
        for w in warnings:
            st.warning(w)
        st.success(f"Store rebuilt — {count:,} unique records.")
        if "df" in st.session_state:
            del st.session_state["df"]
        st.rerun()

with col_snap:
    st.markdown("**Restore a Snapshot**")
    st.caption("Roll back the active store to a previous date. Source files are untouched.")
    snaps = list_snapshots()
    if snaps:
        selected = st.selectbox("Choose snapshot", snaps, label_visibility="collapsed")
        snap_mb = os.path.getsize(os.path.join(SNAP_DIR, selected)) / 1024 / 1024
        st.caption(f"{snap_mb:.1f} MB")
        if st.button("Restore This Snapshot", use_container_width=True):
            restore_snapshot(selected)
            if "df" in st.session_state:
                del st.session_state["df"]
            st.success(f"Restored to {selected}. Reload the app to see the data.")
            st.rerun()
    else:
        st.info("No snapshots yet.")

st.markdown("---")


# ── Auto-load from store ──────────────────────────────────────────────────────
if "df" not in st.session_state:
    stored_now = get_stored_files()
    if stored_now:
        with st.spinner("Loading data..."):
            df, warnings = load_from_store()
        for w in warnings:
            st.warning(w)
        if df is not None:
            st.session_state["df"] = df
            st.rerun()


# ── Summary + diagnostics ─────────────────────────────────────────────────────
if "df" in st.session_state:
    df = st.session_state["df"]

    st.success(
        f"Your analysis is ready — **{len(df):,} records** loaded across "
        f"**{df['redemption_month'].nunique()} months** from **{len(stored)} file(s)**."
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Records", f"{len(df):,}")
    col2.metric(
        "Date Range",
        f"{df['Redemption Date'].min().strftime('%b %Y')} – {df['Redemption Date'].max().strftime('%b %Y')}",
    )
    col3.metric("Unique Brands", df["Brand"].nunique())
    col4.metric("Breakage Records", f"{int(df['is_breakage'].sum()):,}")

    st.markdown("---")

    with st.expander("Diagnostics", expanded=False):
        flagged = int(df["is_breakage"].sum())
        if flagged == 0:
            st.error(
                "No rows are flagged as breakage. "
                "Check that `Final Redemption Status` in your CSV contains 0 for unactivated cards."
            )
        else:
            st.success(f"**{flagged:,} of {len(df):,} rows** flagged as breakage ({flagged / len(df) * 100:.1f}%).")

        st.markdown("#### `Final Redemption Status` value distribution")
        status_counts = (
            df["Final Redemption Status"].value_counts().rename_axis("Value").reset_index(name="Count")
        )
        status_counts["Meaning"] = status_counts["Value"].map({1: "Activated", 0: "Not Activated (Breakage)"})
        st.dataframe(status_counts, use_container_width=True, hide_index=True)

        st.markdown("#### Currency distribution")
        st.dataframe(
            df["Currency"].value_counts().rename_axis("Currency").reset_index(name="Count"),
            use_container_width=True, hide_index=True,
        )

        st.markdown("#### Redemption months")
        st.dataframe(
            df["redemption_month"].astype(str).value_counts().sort_index()
            .rename_axis("Month").reset_index(name="Count"),
            use_container_width=True, hide_index=True,
        )

    st.subheader("Data Preview")
    st.dataframe(
        df[[
            "Reference ID", "Brand", "User_ID", "Company", "Country", "Currency",
            "Amount", "Redemption Date", "Activation Date", "Final Redemption Status",
            "is_activated", "is_breakage", "card_type", "_source_file",
        ]].head(100),
        use_container_width=True,
    )
