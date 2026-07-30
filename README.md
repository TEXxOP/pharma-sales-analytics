# 💊 Pharma Sales Analytics Dashboard

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.45-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Plotly](https://img.shields.io/badge/Plotly-6.1-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)](https://plotly.com)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)

> **An end-to-end pharmaceutical sales analytics dashboard simulating a ZS Associates-style consulting deliverable.** Built to demonstrate SQL mastery (window functions, CTEs, self-joins), Python analytics, and interactive Streamlit dashboarding within a healthcare domain context.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    STREAMLIT DASHBOARD                       │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │Executive│ │Territory │ │   Rep    │ │    Physician     │ │
│  │ Summary │ │  Perf.   │ │Leaderboard│ │   Targeting     │ │
│  └────┬────┘ └────┬─────┘ └────┬─────┘ └────────┬────────┘ │
│  ┌────┴────┐ ┌────┴─────┐                       │          │
│  │Product  │ │   SQL    │                       │          │
│  │Analytics│ │Playground│                       │          │
│  └────┬────┘ └────┬─────┘                       │          │
│       └───────────┼──────────────────────────────┘          │
│                   │  Plotly Interactive Charts               │
└───────────────────┼──────────────────────────────────────────┘
                    │
          ┌─────────┴─────────┐
          │  ANALYTICS LAYER  │
          │  (Python/Pandas)  │
          │  DatabaseManager  │
          │  10 SQL Queries   │
          └─────────┬─────────┘
                    │ SQLAlchemy
          ┌─────────┴─────────┐
          │    POSTGRESQL     │
          │   (Docker)        │
          │                   │
          │  territories (4)  │
          │  reps (20)        │
          │  products (15)    │
          │  physicians (100) │
          │  sales (10,000)   │
          └───────────────────┘
```

---

## 📊 Dashboard Pages

| # | Page | What It Shows | SQL Skills Demonstrated |
|---|------|--------------|------------------------|
| 1 | **Executive Summary** | KPI cards, revenue trends, regional breakdown | Aggregations, date filtering |
| 2 | **Territory Performance** | Heatmap, ranking table, gap analysis | Window functions (RANK), CTEs |
| 3 | **Rep Leaderboard** | Quota attainment, performance tiers, ranking | LAG/LEAD, PARTITION BY |
| 4 | **Physician Targeting** | ABC segmentation, top prescribers | NTILE, CASE statements |
| 5 | **Product Analytics** | Market share, launch trajectory, seasonality | Subqueries, time-series |
| 6 | **SQL Playground** | Custom query runner with 10 pre-built questions | Complex joins, CTEs, window functions |

---

## 🚀 Quick Start

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- Python 3.10+

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/pharma-sales-analytics.git
cd pharma-sales-analytics

# 2. Start PostgreSQL
docker-compose up -d

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Generate synthetic data
python data/generate_data.py

# 5. Seed the database
python data/seed_database.py

# 6. Launch the dashboard
streamlit run dashboard/app.py
```

The dashboard will open at **http://localhost:8501**

---

## 📸 Screenshots

> *Screenshots will be added after deployment*

<!-- 
![Executive Summary](screenshots/executive_summary.png)
![Territory Heatmap](screenshots/territory_heatmap.png)
![Rep Leaderboard](screenshots/rep_leaderboard.png)
![SQL Playground](screenshots/sql_playground.png)
-->

---

## 🔍 10 SQL Queries — Business Problems Solved

Each query is a standalone `.sql` file with detailed comments explaining the business logic and SQL techniques used.

| # | Query | Technique | Business Question |
|---|-------|-----------|-------------------|
| 1 | Revenue Analysis | CTE + LAG | How is each territory growing YoY? |
| 2 | Rep Leaderboard | RANK() + PARTITION BY | Who are the top reps per territory? |
| 3 | Physician ABC | NTILE(3) | How should we segment physicians by value? |
| 4 | Product Share | Subquery + ratio | What's each drug's market share? |
| 5 | Running Averages | ROWS BETWEEN | What's the 3-month sales trend per rep? |
| 6 | Cohort Analysis | DATE_TRUNC + self-join | Do reps hired in Q1 outperform Q3? |
| 7 | Gap Analysis | JOIN + HAVING | Which territories are below target? |
| 8 | Cross-Selling | COUNT DISTINCT + CASE | Which doctors buy multiple categories? |
| 9 | Churn Risk | LAG + threshold | Which physicians are declining? |
| 10 | Trend & Volatility | Moving avg + STDDEV | How stable are monthly revenues? |

---

## 📈 Key Insights from the Data

- **Oncology dominates revenue** despite lower transaction volume — high-value drugs ($500–$2,000/unit) drive disproportionate revenue
- **Q4 revenue spikes 15–20%** consistently across territories, driven by year-end budget utilization
- **Tier A physicians generate ~3x more revenue** than Tier C, validating the ABC segmentation approach
- **Summer months (Jun–Aug) show a 10–15% dip**, suggesting seasonal prescribing patterns
- **Top 20% of reps consistently exceed 120% quota**, while bottom 20% struggle below 70%

---

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Database | PostgreSQL 15 | Normalized relational data storage |
| Container | Docker Compose | Local PostgreSQL deployment |
| Analytics | Python, Pandas, SQLAlchemy | Data processing and query execution |
| Dashboard | Streamlit | Interactive web application |
| Visualization | Plotly | Professional interactive charts |
| Data Generation | Faker | Realistic synthetic data |
| PDF Export | fpdf2 | Executive summary report generation |

---

## 📁 Project Structure

```
pharma-sales-analytics/
├── docker-compose.yml          # PostgreSQL container
├── requirements.txt            # Python dependencies
├── .env                        # Database credentials
├── .gitignore
├── README.md
├── data/
│   ├── generate_data.py        # Synthetic data generator (Faker)
│   └── seed_database.py        # Database seeder
├── sql/
│   ├── schema.sql              # DDL (5 tables with constraints)
│   ├── 01_revenue_analysis.sql # CTE + LAG
│   ├── 02_rep_leaderboard.sql  # RANK() + PARTITION BY
│   ├── 03_physician_abc.sql    # NTILE(3)
│   ├── 04_product_share.sql    # Subquery + ratio
│   ├── 05_running_averages.sql # ROWS BETWEEN
│   ├── 06_cohort_analysis.sql  # DATE_TRUNC + self-join
│   ├── 07_gap_analysis.sql     # JOIN + HAVING
│   ├── 08_cross_sell.sql       # COUNT DISTINCT + CASE
│   ├── 09_churn_risk.sql       # LAG + threshold
│   └── 10_trend_volatility.sql # Moving avg + STDDEV
├── analytics/
│   ├── __init__.py
│   └── queries.py              # DatabaseManager class
└── dashboard/
    └── app.py                  # 6-page Streamlit dashboard
```

---

## 📝 License

This project is for portfolio and educational purposes. Built to demonstrate SQL, Python analytics, and dashboarding skills for healthcare consulting roles.
