# 💿 US CD Market: 20-Year Label Intelligence

![Data Pipeline](https://img.shields.io/badge/Data_Pipeline-Automated-success)
![PostgreSQL](https://img.shields.io/badge/Database-Supabase_PostgreSQL-blue)
![Python](https://img.shields.io/badge/ETL-Python_3.14-yellow)
![BI](https://img.shields.io/badge/BI-Looker_Studio-orange)

👉 **[Click here to view the interactive Looker Studio Dashboard](https://datastudio.google.com/reporting/43cd9c58-bf67-411b-81ac-7126bbeae6b1)**

<img width="1231" height="940" alt="image" src="https://github.com/user-attachments/assets/1dc2e008-53d4-4fa5-92c2-93265430ffc1" />

---

## 📌 Project Overview
This project is an end-to-end data analytics solution designed to evaluate the US CD market over a 20-year span. By extracting data on over **108,000+ music labels** from the Discogs API, the system automatically processes, transforms, and visualizes the delicate balance between market supply (Have) and consumer demand (Want).

The project showcases a full **Modern Data Stack (ELT)** architecture: extracting data via Python, automating the pipeline with GitHub Actions, storing and transforming data in a Supabase PostgreSQL warehouse, and delivering business insights through an interactive Looker Studio dashboard.

---

## 🏗️ Architecture & Technical Pipeline

The data pipeline runs autonomously, updating the analytical models every week.

### 1. Extract & Load (Python)
* **Source:** Discogs API.
* **Process:** A Python script (`extract.py`) paginates through 20 years of US CD releases. It aggregates raw `want` and `have` metrics by label and filters out inactive records.
* **Load:** The aggregated data is pushed directly to a **Supabase (PostgreSQL)** database using `SQLAlchemy`, replacing the raw `label_data` table.

### 2. Automation (GitHub Actions)
* **CI/CD:** The ETL script is orchestrated via GitHub Actions (`run_etl.yml`).
* **Schedule:** Runs automatically every Sunday at 01:00 AM (`cron: '0 1 * * 0'`), ensuring the BI dashboard always reflects the latest market trends.

### 3. Transform (SQL Materialized View)
* **ELT Approach:** Instead of processing metrics in Python, business logic is centralized in the database layer for maximum performance and single-source-of-truth reliability.
* **Execution:** A `MATERIALIZED VIEW` (`label_analytics_view`) calculates all complex metrics. At the end of the Python ETL run, it is automatically refreshed using `REFRESH MATERIALIZED VIEW`.

---

## 🎯 Business Logic & Metric Engineering

A core challenge in assessing label performance is the disparity in scale:
* **Micro-labels** (1-10 releases) easily achieve massive `Want/Have` ratios, artificially inflating their rank.
* **Macro-labels** (Major industry players) have huge market footprints but organically lower ratios due to market saturation.

### 💡 The Solution: Logarithmic "Score" Metric
To create a fair evaluation, a custom metric was engineered using SQL. It applies a **base-10 logarithmic smoothing factor** based on the total market size, effectively compensating for the natural drop in demand ratios as labels grow.

**Core SQL Transformations:**
```sql
-- 1. Want to Have Ratio (Protecting against Division by Zero)
ROUND((want::numeric / CASE WHEN have = 0 THEN 1 ELSE have END), 4) AS want_to_have_ratio

-- 2. Overall Performance Score
-- Ratio scaled by the Log10 of the Market Size (Want + Have)
ROUND(
    (want::numeric / CASE WHEN have = 0 THEN 1 ELSE have END) * 
    LOG(10, CASE WHEN (want + have) < 10 THEN 10 ELSE (want + have) END), 
4) AS score

-- 3. Component Scores
-- Score Demand and Score Supply isolate the specific impacts of user wishlists vs. actual inventory.
```
*(Lower bounds of 10 are enforced for log calculations to prevent negative multipliers for micro-labels).*

---

## 📊 Business Intelligence (Looker Studio)

The resulting materialized view is connected to a **Looker Studio Dashboard**, providing an executive overview of the market.

**Dashboard Features:**
1. **Interactive Parameters:** Users can dynamically sort all visualizations simultaneously using a custom UI control (`Sort Option` & `Sort Direction`) backed by a SQL `CASE` statement.
2. **Performance Ranking:** A Top 100 heat-mapped table highlighting absolute score vs. relative ratio.
3. **Efficiency Benchmarking:** Bar charts grouped by `Market Size Bins` (e.g., `01. 1-10`, `02. 11-100`, up to `> 100,000`), proving that the logarithmic `Score` successfully standardizes evaluation across drastically different business sizes.

---

## 🚀 How to Run Locally

1. **Create a project database.**
2. **Create a materialized view in the database using `setup_mview.sql`.**
3. **Clone the repository and install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Set up Environment Variables:**
   Create a `.env` file with your credentials:
   ```env
   DISCOGS_TOKEN=your_personal_access_token
   DATABASE_URL=postgresql://user:password@aws-0-eu-central-1.pooler.supabase.com:6543/postgres
   ```
4. **Run the ETL Pipeline:**
   ```bash
   python extract.py
   ```
