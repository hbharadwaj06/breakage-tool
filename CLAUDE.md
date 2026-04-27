# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app (opens at http://localhost:8501)
streamlit run app.py

# User management
python3 scripts/manage_users.py list
python3 scripts/manage_users.py add <username> "<Full Name>" <admin|viewer>
python3 scripts/manage_users.py set-password <username>
python3 scripts/manage_users.py remove <username>

# First-time setup
cp config/users.example.json config/users.json
python3 scripts/manage_users.py set-password admin
```

## Architecture

**Streamlit multi-page app.** `app.py` is the sole entry point — it enforces login via `modules/auth.require_login()`, conditionally adds the Upload page for admins, then delegates to `st.navigation()`. Every page file calls `require_login()` itself as a guard.

### Module responsibilities

| Module | Role |
|--------|------|
| `modules/loader.py` | CSV ingestion, cleaning, deduplication, disk persistence (`data/`), filter application |
| `modules/calculator.py` | All business logic: KPIs, monthly/weekly trends, maturity threshold, cohort matrix, survival curves, insight generation |
| `modules/charts.py` | Pure Plotly chart builder functions (no side effects, no Streamlit calls) |
| `modules/fx.py` | Live USD exchange rates via open.er-api.com, cached per session-day, with manual fallback |
| `modules/exporter.py` | Multi-sheet Excel workbook builder |
| `modules/reporter.py` | HTML print-to-PDF report generator |
| `modules/auth.py` | SHA-256 password check against `config/users.json`, Streamlit session state auth |

### Data flow

1. Admin uploads CSVs on the Upload page → `loader.save_uploaded_file()` writes them to `data/`
2. On every page load, `loader.load_from_store()` reads all CSVs in `data/`, merges them, and deduplicates
3. `loader._clean()` adds derived columns: `composite_key`, `is_activated`, `is_breakage`, `activation_lag_days`, `redemption_month`, `activation_month`, `card_type`
4. Pages call `calculator.*` functions with the merged DataFrame; charts are built by `charts.*` and rendered via `st.plotly_chart()`

### Critical domain rules

**Breakage definition:** `Final Redemption Status == 0` (integer). This column is always 0 or 1 — never a string. `is_breakage = (Final Redemption Status == 0)`, `is_activated = (Final Redemption Status == 1)`.

**Deduplication — "activated wins":** The same card can appear as status 0 in one file and status 1 in a later update file. `loader._dedup()` sorts descending on `Final Redemption Status` then `drop_duplicates(subset=["composite_key"], keep="first")` — so the activated record always survives.

**Composite key:** `Reference ID + "|" + User_ID + "|" + Brand`. Reference IDs are server-scoped (the same integer can identify different cards on different servers), so the composite key is required for correct deduplication.

**Maturity / right-censoring:** Recent cohorts always show artificially high breakage because employees haven't had time to click yet. `calculator.maturity_threshold_days()` computes the day at which 95% of historical activations occurred (from cohorts redeemed 180+ days ago). `calculator.preliminary_months()` returns the set of months still within that window. Preliminary months are **excluded from all trend direction statements, MoM deltas, and insight summaries**.

**Multi-currency:** Amounts are never mixed. Every function that returns monetary values takes an explicit `currency` parameter and filters `df["Currency"] == currency` before summing.

**Card type:** Only Visa and Mastercard are `open_loop`; everything else defaults to `closed_loop`. Mapping lives in `config/brand_types.json`.

### Authentication & roles

Two roles: `admin` (can upload data) and `viewer` (read-only). Auth state lives in Streamlit session state under `_auth_user`, `_auth_role`, `_auth_name`. `config/users.json` is gitignored and must be created locally.

### Persistence

Uploaded CSVs are written to `data/` (gitignored). The app auto-loads all files from `data/` on every startup — no re-upload needed for historical data.
