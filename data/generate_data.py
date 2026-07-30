"""
Pharma Sales Analytics — Synthetic Data Generator
===================================================
Generates realistic pharmaceutical sales data using Faker.

Business-realistic patterns built in:
  • Cardiology:  high volume (50–200 units), lower price ($50–$200)
  • Oncology:    low volume (5–30 units), higher price ($500–$2,000)
  • Neurology:   medium volume (20–80 units), medium price ($150–$500)
  • Tier A physicians get 3x more transactions and higher quantities
  • Seasonal: Q4 spike (+20%), summer dip (–15%)
  • Top/bottom performer variance among reps

Output: CSV files in data/ folder + console summary.
"""

import os
import random
import csv
from datetime import date, timedelta
from pathlib import Path

from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)

DATA_DIR = Path(__file__).parent

# ============================================================
# 1. TERRITORIES
# ============================================================
TERRITORIES = [
    {"territory_id": 1, "name": "Northeast Corridor",  "region": "North", "manager": "Sarah Mitchell"},
    {"territory_id": 2, "name": "Southeast Hub",        "region": "South", "manager": "James Rodriguez"},
    {"territory_id": 3, "name": "Pacific West",         "region": "West",  "manager": "Linda Chen"},
    {"territory_id": 4, "name": "Great Lakes",          "region": "East",  "manager": "Robert Williams"},
]

# ============================================================
# 2. PRODUCTS (15 drugs across 3 categories)
# ============================================================
PRODUCT_TEMPLATES = {
    "Cardiology": [
        ("Cardivex",      80.00,  date(2020, 3, 15)),
        ("Heartguard",   120.00,  date(2019, 7, 1)),
        ("Vasoprime",    150.00,  date(2021, 1, 10)),
        ("Arterixin",     65.00,  date(2022, 6, 20)),
        ("Rhythmol Plus",195.00,  date(2023, 9, 5)),
    ],
    "Oncology": [
        ("OncoShield",   1200.00, date(2020, 11, 1)),
        ("TumorHalt",     850.00, date(2021, 4, 15)),
        ("CellGuard Pro", 1800.00, date(2022, 2, 28)),
        ("ImmunoPlex",    950.00, date(2019, 8, 12)),
        ("NeoBlock",     1500.00, date(2023, 5, 1)),
    ],
    "Neurology": [
        ("NeuroCalm",    250.00,  date(2020, 5, 20)),
        ("SynaptiX",     350.00,  date(2021, 9, 1)),
        ("MindShield",   180.00,  date(2019, 12, 10)),
        ("CortexEase",   420.00,  date(2022, 8, 15)),
        ("AxonRestore",  300.00,  date(2023, 11, 1)),
    ],
}

products = []
pid = 1
for category, drugs in PRODUCT_TEMPLATES.items():
    for name, price, launch in drugs:
        products.append({
            "product_id": pid,
            "name": name,
            "category": category,
            "price_per_unit": price,
            "launch_date": launch.isoformat(),
        })
        pid += 1

# ============================================================
# 3. REPS (20 reps — 5 per territory)
# ============================================================
# Performance multiplier: some reps are top performers, some lag
REP_PERFORMANCE = {}  # rep_id -> multiplier (0.6 to 1.4)

reps = []
rep_id = 1
for t in TERRITORIES:
    for i in range(5):
        hire_year = random.choice([2021, 2021, 2022, 2022, 2023, 2023, 2024])
        hire_month = random.randint(1, 12)
        hire_day = random.randint(1, 28)
        hd = date(hire_year, hire_month, hire_day)

        # Quota scales by seniority (earlier hire → higher quota)
        years_tenure = max(1, 2025 - hire_year)
        base_quota = random.randint(400000, 600000)
        quota = round(base_quota * (1 + 0.1 * years_tenure), 2)

        # Performance multiplier
        perf = round(random.uniform(0.6, 1.5), 2)
        REP_PERFORMANCE[rep_id] = perf

        reps.append({
            "rep_id": rep_id,
            "name": fake.name(),
            "territory_id": t["territory_id"],
            "hire_date": hd.isoformat(),
            "target_quota": quota,
        })
        rep_id += 1

# ============================================================
# 4. PHYSICIANS (100 doctors)
# ============================================================
SPECIALTIES = {
    "Cardiology": ["Cardiologist", "Interventional Cardiologist", "Electrophysiologist"],
    "Oncology":   ["Medical Oncologist", "Surgical Oncologist", "Radiation Oncologist"],
    "Neurology":  ["Neurologist", "Neurosurgeon", "Neuro-Oncologist"],
}
ALL_SPECIALTIES = [s for specs in SPECIALTIES.values() for s in specs]

HOSPITALS = [
    "Mount Sinai Medical Center", "Johns Hopkins Hospital", "Mayo Clinic",
    "Cleveland Clinic", "Massachusetts General Hospital", "Stanford Health",
    "Cedars-Sinai Medical Center", "Duke University Hospital",
    "UCSF Medical Center", "Northwestern Memorial Hospital",
    "NYU Langone Health", "Brigham and Women's Hospital",
    "University of Chicago Medical Center", "Emory University Hospital",
    "Houston Methodist Hospital",
]

physicians = []
# Tier distribution: A=20%, B=30%, C=50%
tier_pool = ["A"] * 20 + ["B"] * 30 + ["C"] * 50

for phys_id in range(1, 101):
    territory = random.choice(TERRITORIES)
    specialty = random.choice(ALL_SPECIALTIES)
    tier = random.choice(tier_pool)
    hospital = random.choice(HOSPITALS)

    physicians.append({
        "physician_id": phys_id,
        "name": f"Dr. {fake.last_name()}",
        "specialty": specialty,
        "territory_id": territory["territory_id"],
        "tier": tier,
        "hospital_affiliation": hospital,
    })

# ============================================================
# 5. SALES TRANSACTIONS (10,000 records, Jan 2023 – Dec 2025)
# ============================================================
START_DATE = date(2023, 1, 1)
END_DATE   = date(2025, 12, 31)
TOTAL_DAYS = (END_DATE - START_DATE).days

# Category-specific quantity ranges
QTY_RANGES = {
    "Cardiology": (50, 200),
    "Oncology":   (5, 30),
    "Neurology":  (20, 80),
}

# Seasonal multipliers by month (1-indexed)
SEASONAL = {
    1: 0.95,   # Jan — post-holiday slow
    2: 0.98,
    3: 1.02,
    4: 1.05,
    5: 1.00,
    6: 0.88,   # Summer dip
    7: 0.85,   # Summer dip
    8: 0.90,
    9: 1.05,   # Back-to-business
    10: 1.10,
    11: 1.15,  # Q4 spike
    12: 1.20,  # Q4 spike — year-end push
}

# Tier-based transaction probability weights
TIER_WEIGHT = {"A": 3.0, "B": 1.5, "C": 0.8}
TIER_QTY_MULT = {"A": 1.5, "B": 1.0, "C": 0.7}

# Build lookup maps
product_map = {p["product_id"]: p for p in products}
physician_map = {p["physician_id"]: p for p in physicians}
rep_territory = {r["rep_id"]: r["territory_id"] for r in reps}

# Pre-compute physician weights for weighted selection
phys_weights = [TIER_WEIGHT[p["tier"]] for p in physicians]
phys_ids = [p["physician_id"] for p in physicians]

sales = []
sale_id = 1

print("Generating 10,000 sales transactions...")

while sale_id <= 10000:
    # Random date
    day_offset = random.randint(0, TOTAL_DAYS)
    sale_date = START_DATE + timedelta(days=day_offset)

    # Only generate sales for products launched before the sale date
    eligible_products = [
        p for p in products
        if date.fromisoformat(p["launch_date"]) <= sale_date
    ]
    if not eligible_products:
        continue

    product = random.choice(eligible_products)
    category = product["category"]

    # Weighted physician selection (Tier A gets more)
    physician = random.choices(physicians, weights=phys_weights, k=1)[0]

    # Pick a rep from same territory as physician
    territory_reps = [r for r in reps if r["territory_id"] == physician["territory_id"]]
    rep = random.choice(territory_reps)

    # Base quantity from category range
    qty_low, qty_high = QTY_RANGES[category]
    base_qty = random.randint(qty_low, qty_high)

    # Apply tier multiplier
    qty = max(1, int(base_qty * TIER_QTY_MULT[physician["tier"]]))

    # Apply seasonal multiplier
    seasonal_mult = SEASONAL[sale_date.month]
    qty = max(1, int(qty * seasonal_mult))

    # Apply rep performance multiplier
    perf_mult = REP_PERFORMANCE[rep["rep_id"]]
    qty = max(1, int(qty * perf_mult))

    # Amount = quantity × price_per_unit
    amount = round(qty * product["price_per_unit"], 2)

    sales.append({
        "sale_id": sale_id,
        "rep_id": rep["rep_id"],
        "physician_id": physician["physician_id"],
        "product_id": product["product_id"],
        "quantity": qty,
        "sale_date": sale_date.isoformat(),
        "amount": amount,
    })
    sale_id += 1

# ============================================================
# WRITE CSV FILES
# ============================================================
def write_csv(filename, data, fieldnames):
    filepath = DATA_DIR / filename
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    print(f"  [OK] {filename}: {len(data)} rows")

print("\nWriting CSV files...")
write_csv("territories.csv", TERRITORIES, ["territory_id", "name", "region", "manager"])
write_csv("reps.csv", reps, ["rep_id", "name", "territory_id", "hire_date", "target_quota"])
write_csv("products.csv", products, ["product_id", "name", "category", "price_per_unit", "launch_date"])
write_csv("physicians.csv", physicians, ["physician_id", "name", "specialty", "territory_id", "tier", "hospital_affiliation"])
write_csv("sales.csv", sales, ["sale_id", "rep_id", "physician_id", "product_id", "quantity", "sale_date", "amount"])

# ============================================================
# SUMMARY STATISTICS
# ============================================================
total_revenue = sum(s["amount"] for s in sales)
avg_deal = total_revenue / len(sales)
categories_rev = {}
for s in sales:
    cat = product_map[s["product_id"]]["category"]
    categories_rev[cat] = categories_rev.get(cat, 0) + s["amount"]

print(f"\n{'='*50}")
print(f"DATA GENERATION COMPLETE")
print(f"{'='*50}")
print(f"  Total Revenue:      ${total_revenue:,.2f}")
print(f"  Avg Deal Size:      ${avg_deal:,.2f}")
print(f"  Transactions:       {len(sales):,}")
print(f"  Date Range:         {START_DATE} -> {END_DATE}")
print(f"\n  Revenue by Category:")
for cat, rev in sorted(categories_rev.items()):
    print(f"    {cat:15s}  ${rev:>14,.2f}")
print(f"{'='*50}")
