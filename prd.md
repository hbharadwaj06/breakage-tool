# Product Requirements Document
# Breakage Analysis Tool — Vantage Circle

**Version:** 1.0  
**Owner:** Hemanga Bharadwaj  
**Last Updated:** April 2026  
**Status:** Active Development

---

## 1. Product Overview

The Breakage Analysis Tool is an internal analytics dashboard for Vantage Circle's finance and leadership team. It processes monthly gift card redemption data from multiple geographic servers, calculates breakage metrics (unrealized cost from unactivated gift cards), and surfaces actionable insights for the CEO and finance team.

The tool is designed to run as a hosted web application with role-based access control — administrators upload and manage data, viewers consume insights and reports.

---

## 2. Business Context

Since November 2024, Vantage Circle switched to a **click-to-activate model** for gift card fulfillment:

- Employee redeems points → receives an email with an activation link
- Supplier API is called **only when the employee clicks the link**
- If the employee never clicks → Vantage Circle never pays the supplier → the unrealized cost = **breakage revenue**

**Breakage is financially positive.** Higher breakage rate means more unrealized cost Vantage Circle does not incur. The tool tracks, analyzes, and forecasts this breakage across currencies, clients, card types, and time periods.

**Data source:** Monthly CSV exports from 4 geographic servers (NYC and others), each containing redemption and activation records.

---

## 3. User Personas & Roles

| Role | User | Access | Responsibilities |
|------|------|--------|-----------------|
| **Admin** | Hemanga Bharadwaj | Full access — all pages including Upload | Upload monthly data, manage users, maintain data quality |
| **Viewer** | CEO, Finance Head, Leadership | Read-only — all analysis pages, no Upload | Consume insights, generate reports, ask business questions |

### Access Control Rules
- Only `admin` role can access the Upload Data page
- All other pages (Overview, Breakage, Behavior, Insights, Export) are accessible to all authenticated roles
- Authentication is required before any page loads
- Sessions are terminated on browser close or manual sign-out

---

## 4. Current Feature Set

### Page 1 · Upload Data *(Admin only)*
- Multi-file CSV uploader (1–N files per session)
- Files persisted to `data/` directory — survive app restarts
- Auto-loads all stored files on startup — admin only needs to upload new months
- Per-file delete with confirmation
- Deduplication on upload: activated status always wins over unactivated for the same card
- Diagnostics: `Final Redemption Status` distribution, currency breakdown, month coverage
- Data preview (first 100 rows)

### Page 2 · Overview
- **KPI row:** Total Breakage Amount, Breakage Rate %, Total Activated Amount, Total Redeemed Amount
- **MoM deltas:** Compared against last two settled (mature) cohorts only
- **Breakage rate trend:** Area chart with grey shading over preliminary months
- **Monthly breakage amount:** Bar chart per redemption month
- **Week-on-week breakage rate:** Shown when 3+ weeks of data are in range
- **Key Insights:** Auto-generated bullet summary (mature cohorts only)
- **Filters:** Currency, redemption month range, company

### Page 3 · Breakage Deep-Dive
- **By Client:** Horizontal bar chart, ranked by breakage amount; ⚠️ flag for clients >1.3× average rate
- **By Denomination:** Currency-aware buckets (INR scale, USD scale, etc.); amount + count charts
- **By Card Type:** Open loop vs closed loop — donut + data table
- **By Brand:** Horizontal bar, configurable top-N slider
- **By Country:** Treemap with breakage rate color scale
- **Filters:** Currency, month range, company

### Page 4 · Behavior
- **Cohort Activation Matrix:** Redemption month × activation month heatmap; toggle between % and currency amount; `~` prefix on preliminary cohorts
- **Activation Decay / Survival Curves:** Per-cohort % still unactivated at days 1, 7, 14, 30, 60, 90, 180
- **Activation Timing Heatmap:** Day-of-week × hour-of-day activation density
- **Activation Lag Histogram:** Distribution of days to activate for all activated cards
- **Filters:** Currency, month range, company

### Page 5 · Insights *(CEO Briefing)*
- Auto-generated structured insights from `generate_full_insights()`
- **Sections:** Overview Summary, This Month, Trends, Clients to Watch, What's Driving Breakage, Forecast
- Preliminary months flagged with ⚠️ — never used as trend evidence
- Color-coded insight cards: green (positive), blue (neutral), red (alert), orange (forecast)
- Print-ready layout

### Page 6 · Export & Report
- **Excel export:** 7-sheet workbook — Raw Data, Monthly Summary, By Brand, By Denomination, By Country, By Card Type, Cohort Table
- **HTML report:** Print-ready HTML file; open in browser → Cmd+P → Save as PDF
- Report includes: Cover page, Executive Summary (KPIs), Key Findings, Monthly Trend table, Client Breakdown, Cohort Table, Denomination breakdown

---

## 5. Data Model

### Source CSV Columns
```
Reference ID | Deal ID | Brand | User_ID | Company | Country | Currency |
Amount | Points | Redemption Status | Redemption Date | Activation Date |
Final Redemption Status
```

### Key Semantics
| Column | Meaning |
|--------|---------|
| `Final Redemption Status` | **1** = activated, **0** = not activated (breakage) |
| `Redemption Status` | Always 1 — ignore for breakage logic |
| `Activation Date` | Populated only when activated; null = never clicked |
| `Reference ID` | Server-scoped — same ID can exist on multiple servers |

### Derived Fields
| Field | Logic |
|-------|-------|
| `composite_key` | `Reference ID + "\|" + User_ID + "\|" + Brand` |
| `is_activated` | `Final Redemption Status == 1` |
| `is_breakage` | `Final Redemption Status == 0` |
| `activation_lag_days` | `Activation Date − Redemption Date` in days |
| `redemption_month` | `pd.Period(Redemption Date, "M")` |
| `card_type` | Mapped from `config/brand_types.json`; default `closed_loop` |

### Deduplication
Activated status always wins. Sort descending on `Final Redemption Status`, then `drop_duplicates(composite_key, keep="first")`. This handles cross-server duplicates and incremental status updates (0→1) correctly.

---

## 6. Maturity & Right-Censoring

Recent redemption months always appear to have inflated breakage because the activation window is still open. The tool handles this with a **dynamic maturity threshold**:

1. Takes only cohorts redeemed 180+ days ago (fully settled)
2. Finds the day at which 95% of all activations from those settled cohorts had occurred
3. Marks any redemption month within that many days of the latest date as **preliminary**

Preliminary months are:
- Shaded grey in the trend chart
- Excluded from MoM delta calculations
- Marked with `~` in the cohort matrix
- Flagged with ⚠️ in Insights
- Never used as evidence of a trend direction

---

## 7. Security & Access Control

### Authentication
- Username + password login required before any page loads
- Passwords stored as SHA-256 hashes in `config/users.json`
- Sessions held in Streamlit session state; cleared on sign-out or browser close

### User Management
Users are managed via CLI:
```bash
python scripts/manage_users.py list
python scripts/manage_users.py add <username> <name> <role>
python scripts/manage_users.py set-password <username>
python scripts/manage_users.py remove <username>
```

### Roles
| Role | Upload | Overview | Breakage | Behavior | Insights | Export |
|------|--------|----------|----------|----------|----------|--------|
| admin | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| viewer | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |

Upload page is hidden from the navigation entirely for viewer-role users.

---

## 8. Hosting Recommendations

### Recommended (Secure, ~$15–20/month)
- **Compute:** AWS EC2 / GCP Compute Engine / Azure VM (t3.small or equivalent)
- **Auth:** Streamlit's built-in login + users.json (already implemented)
- **HTTPS:** Reverse proxy via Caddy or Nginx + Let's Encrypt (free SSL)
- **Data storage:** Local disk on the VM, or private S3/GCS bucket
- **Access:** IP allowlist at firewall level for additional security

### Alternative (Free, lower security boundary)
- **Streamlit Community Cloud** — restrict access to specific email addresses
- Data lives on Streamlit's infrastructure (owned by Snowflake)
- Acceptable for non-GDPR-critical data and teams already using SaaS tools

---

## 9. Tech Stack

| Layer | Library | Reason |
|-------|---------|--------|
| UI | Streamlit 1.50+ | File upload, filters, charts, multi-page, built-in auth support |
| Data | Pandas | CSV merge, dedup, all aggregations |
| Charts | Plotly | Interactive, filterable, embeds natively in Streamlit |
| Excel export | openpyxl | Multi-sheet workbook |
| HTML report | Pure Python string | No dependencies, renders in browser, Cmd+P → PDF |
| Auth | hashlib (SHA-256) | Lightweight, no external dependency |

---

## 10. Known Limitations

| Limitation | Notes |
|------------|-------|
| No cross-currency totals | Mixing INR and USD is meaningless; each currency always analysed separately |
| Forecast is linear | Projects breakage using avg mature activation rate; no seasonality or client-specific curves |
| Anomaly detection not built | Flagging companies that spiked *this specific month* vs historical is not yet implemented |
| Week-on-week requires 3+ weeks | Chart hidden if fewer than 3 complete weeks in the filtered range |

---

## 11. Proposed Enhancements

### 11.1 Quick Query Panel
**Priority:** High  
**Status:** Proposed  
**Description:** A collapsible panel on the Overview page with direct date-range inputs (month dropdowns, not a slider) and a currency selector. Returns an instant answer card: breakage amount, count, and rate for the exact period specified — without requiring users to navigate sliders.  
**Use case:** "Tell me the total INR breakage from April 2025 to September 2025."  
**Effort:** Low (1–2 hours). Pure UI change, no new calculations needed.

---

### 11.2 Natural Language Query Interface ("Ask AI")
**Priority:** Medium  
**Status:** Proposed — skipped for v1, planned for v2  
**Description:** A text input where any user (including the CEO) can type a business question in plain English and receive a direct, contextual answer.

**Example queries:**
- "What is the INR breakage for H1 2025?"
- "Which company is driving the most breakage this quarter?"
- "Is the trend improving or worsening?"
- "If 10% more employees activated, how much less breakage would we have?"

**Proposed architecture:**
1. User types a question
2. App assembles a **data context summary** — KPIs, trend, company breakdown, card type split, preliminary months, active filters (aggregated, not raw rows)
3. Sends question + context to an LLM API
4. Returns a plain-English answer in the UI

**LLM options considered:**

| Option | Cost | Hosted | Privacy | Notes |
|--------|------|--------|---------|-------|
| Groq (Llama 3) | Free tier (generous) | Cloud | Standard SaaS | Best for hosted app, very fast |
| Anthropic Claude API | Pay-per-use (~cents/query) | Cloud | Strong — no training on API data | Best answer quality + privacy policy |
| Ollama (local) | Free forever | Self-hosted VM | Best — data never leaves server | Requires VM with 8GB+ RAM; not suitable for Streamlit Cloud |

**Security note:** Even with aggregated context (no raw rows), company names and breakage amounts are included in the API call. Ollama on a private VM is the only option where zero data leaves the infrastructure.

**Decision for v1:** Skipped. Will be implemented in v2 once hosting architecture is confirmed and data privacy requirements are finalized.

**Effort estimate:** Medium (1–2 days). Requires API key management, context assembly, UI, and error handling for rate limits.

---

### 11.3 Anomaly Detection
**Priority:** Medium  
**Status:** Proposed  
**Description:** Automatically flag companies or brands whose breakage rate spiked significantly in the most recent settled month vs their own historical average. Surfaces in the Breakage page and Insights.  
**Effort:** Medium (half day). Calculation is straightforward; display is the main work.

---

### 11.4 Currency-Aware Forecast
**Priority:** Low  
**Status:** Proposed  
**Description:** Replace the current linear forecast (average mature activation rate × open cards) with a per-client and per-card-type model that accounts for the different activation curves of open loop vs closed loop cards.  
**Effort:** Medium (1 day).

---

## 12. Decisions Log

| Date | Decision | Reason |
|------|----------|--------|
| Apr 2026 | Composite key for dedup (Reference ID + User_ID + Brand) | Reference IDs are server-scoped; same ID can appear across geographies for different cards |
| Apr 2026 | Breakage = Final Redemption Status == 0 (integer) | Column is binary integer (0/1); earlier string-matching caused all charts to be blank |
| Apr 2026 | Activated wins in dedup | Status updates (0→1) arrive in incremental uploads; must overwrite old record |
| Apr 2026 | Dynamic maturity threshold at 95th percentile of activation lag | Hardcoded windows are arbitrary; data-driven threshold adapts as activation patterns change |
| Apr 2026 | HTML print-to-PDF instead of programmatic PDF | No kaleido/reportlab dependency; output is cleaner; user controls print settings |
| Apr 2026 | Exclude preliminary months from insights/trend direction | Recent cohorts are right-censored — including them creates false "worsening" signals |
| Apr 2026 | "Breakage" as primary label, "Not Activated" in data table status columns | "Breakage" is the financial industry term; "Not Activated" is the operational status |
| Apr 2026 | Currency-aware denomination buckets | INR-scale buckets are meaningless for USD/CAD data |
| Apr 2026 | Role-based access — admin-only Upload page | Only the data owner should control what data enters the system |
| Apr 2026 | Skip AI query interface for v1 | Hosting architecture and data privacy requirements not yet finalized; adds complexity without resolving the security question first |
| Apr 2026 | SHA-256 password hashing in users.json | Lightweight, no external dependency; sufficient for an internal tool |
