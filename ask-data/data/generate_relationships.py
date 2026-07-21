"""
Generate customer_relationships.csv — synthetic graph edges for risk propagation demo.

Relationship types:
  - co_borrower    : shared loan / joint policy
  - guarantor      : one customer guarantees another's policy
  - same_employer  : work at the same company (layoff risk propagation)
  - same_branch    : registered at the same branch (regional risk cluster)

Output: customer_relationships.csv
  customer_id | related_customer_id | relationship_type | risk_weight | is_active
"""

import csv
import random
from collections import defaultdict
from pathlib import Path

random.seed(99)

SRC = Path("/Users/trianonurhikmat/Documents/Works/cloudera/account/data intelligence/ask-data/data/sample_data_parquet/customer360_agent_studio_demo.csv")
OUT = Path("/Users/trianonurhikmat/Documents/Works/cloudera/account/data intelligence/ask-data/data/sample_data_parquet/customer_relationships.csv")

# ── Load customers ─────────────────────────────────────────────────────────────
with open(SRC) as f:
    rows = list(csv.DictReader(f))

all_ids      = [r["customer_id"] for r in rows]
by_province  = defaultdict(list)
by_segment   = defaultdict(list)
high_risk    = []

for r in rows:
    by_province[r["province"]].append(r["customer_id"])
    by_segment[r["segment"]].append(r["customer_id"])
    if float(r["churn_risk"]) >= 0.60:
        high_risk.append(r["customer_id"])

# ── Relationship config ────────────────────────────────────────────────────────
# risk_weight: how strongly risk propagates through this edge (0.0–1.0)
REL_CONFIGS = {
    "co_borrower":   {"weight_range": (0.70, 0.95), "count": 800},
    "guarantor":     {"weight_range": (0.80, 0.99), "count": 600},
    "same_employer": {"weight_range": (0.30, 0.60), "count": 1200},
    "same_branch":   {"weight_range": (0.10, 0.35), "count": 1500},
}

edges = set()   # (a, b, type) — deduplicate
results = []

def add_edge(a, b, rel_type, weight):
    key = (min(a, b), max(a, b), rel_type)
    if key in edges or a == b:
        return False
    edges.add(key)
    results.append({
        "customer_id":         a,
        "related_customer_id": b,
        "relationship_type":   rel_type,
        "risk_weight":         round(weight, 3),
        "is_active":           random.choice(["true", "true", "true", "false"]),  # 75% active
    })
    return True

# ── co_borrower: high-risk customers paired with others ───────────────────────
cfg = REL_CONFIGS["co_borrower"]
attempts = 0
while len([r for r in results if r["relationship_type"] == "co_borrower"]) < cfg["count"] and attempts < 10000:
    a = random.choice(high_risk)
    b = random.choice(all_ids)
    w = random.uniform(*cfg["weight_range"])
    add_edge(a, b, "co_borrower", w)
    attempts += 1

# ── guarantor: At Risk customers guaranteed by Standard/Growth ────────────────
at_risk_ids  = by_segment["At Risk"]
stable_ids   = by_segment["Standard"] + by_segment["Growth"] + by_segment["Premium"]
cfg = REL_CONFIGS["guarantor"]
attempts = 0
while len([r for r in results if r["relationship_type"] == "guarantor"]) < cfg["count"] and attempts < 10000:
    debtor    = random.choice(at_risk_ids)
    guarantor = random.choice(stable_ids)
    w = random.uniform(*cfg["weight_range"])
    add_edge(debtor, guarantor, "guarantor", w)
    attempts += 1

# ── same_employer: cluster by province (proxy for employer) ───────────────────
cfg = REL_CONFIGS["same_employer"]
attempts = 0
while len([r for r in results if r["relationship_type"] == "same_employer"]) < cfg["count"] and attempts < 20000:
    province = random.choice(list(by_province.keys()))
    pool = by_province[province]
    if len(pool) < 2:
        attempts += 1
        continue
    a, b = random.sample(pool, 2)
    w = random.uniform(*cfg["weight_range"])
    add_edge(a, b, "same_employer", w)
    attempts += 1

# ── same_branch: wider regional cluster ───────────────────────────────────────
cfg = REL_CONFIGS["same_branch"]
attempts = 0
while len([r for r in results if r["relationship_type"] == "same_branch"]) < cfg["count"] and attempts < 20000:
    province = random.choice(list(by_province.keys()))
    pool = by_province[province]
    if len(pool) < 2:
        attempts += 1
        continue
    a, b = random.sample(pool, 2)
    w = random.uniform(*cfg["weight_range"])
    add_edge(a, b, "same_branch", w)
    attempts += 1

# ── Write output ───────────────────────────────────────────────────────────────
FIELDNAMES = ["customer_id", "related_customer_id", "relationship_type", "risk_weight", "is_active"]

with open(OUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
    writer.writeheader()
    writer.writerows(results)

# ── Summary ───────────────────────────────────────────────────────────────────
from collections import Counter
type_counts = Counter(r["relationship_type"] for r in results)
print(f"Total edges   : {len(results)}")
print(f"By type       : {dict(type_counts)}")
print(f"Unique pairs  : {len(edges)}")
print(f"Output        : {OUT}")
print()
print("Sample rows:")
for r in results[:5]:
    print(f"  {r}")
