# Setup Guide — Breakage Analysis Tool

## Prerequisites

- Python 3.9 or higher — check with `python3 --version`
- pip (comes with Python)

---

## Step 1 — Clone the repository

Open Terminal and run:

```bash
git clone https://github.com/hbharadwaj06/breakage-tool.git
cd breakage-tool
```

---

## Step 2 — Install dependencies

```bash
pip install -r requirements.txt
```

This installs Streamlit, Pandas, Plotly, openpyxl, and requests.

---

## Step 3 — Create your login credentials

The repo does not include real user accounts. You need to create your own local `users.json`:

```bash
cp config/users.example.json config/users.json
python3 scripts/manage_users.py set-password admin
```

When prompted, type a password for the `admin` account. This account has full access including data upload.

To add more users or change roles:

```bash
# List existing users
python3 scripts/manage_users.py list

# Add a new viewer (read-only)
python3 scripts/manage_users.py add ceo "CEO Name" viewer
python3 scripts/manage_users.py set-password ceo

# Remove a user
python3 scripts/manage_users.py remove username
```

> **Important:** `config/users.json` is in `.gitignore` — it will never be committed. Keep it local.

---

## Step 4 — Run the app

```bash
streamlit run app.py
```

The app will open automatically in your browser at `http://localhost:8501`.

Log in with the `admin` credentials you set in Step 3.

---

## Step 5 — Upload data

1. Go to the **Upload Data** page (admin only)
2. Upload your CSV files — the app accepts multiple files at once
3. Once uploaded, all other pages populate automatically

> **Data stays local.** The `data/` folder is in `.gitignore` — your CSVs are never committed to GitHub.

---

## Monthly workflow

Each month you receive 6 files (2 per server × 3 servers):
- **New records file** — fresh redemptions for the current month
- **Status updates file** — previous-month cards that have since been activated

Upload all 6 on the Upload page. The app merges and deduplicates automatically — the same card is never double-counted even if it appears across multiple files.

---

## Pulling the latest code changes

When the codebase is updated, sync your local copy:

```bash
git pull origin main
```

Your `data/` folder and `config/users.json` are untouched by pulls.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `streamlit: command not found` | Run `pip install streamlit` or use `python3 -m streamlit run app.py` |
| Login screen shows but login fails | Check that `config/users.json` exists and password was set via `manage_users.py` |
| "No data loaded" on all pages | Go to Upload page first and upload at least one CSV |
| Exchange rates not loading (Global View) | Check internet connection — the app will show a manual rate entry form as fallback |
| Missing columns error on upload | Ensure your CSV has all required columns — see `modules/loader.py` for the full list |
