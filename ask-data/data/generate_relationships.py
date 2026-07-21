"""
Generate customer_relationships.csv — synthetic graph edges for risk propagation demo.

Aligned to customer_dormant_segment.csv (CUST000000001 format, 10k rows) —
NOT customer360_agent_studio_demo.csv. This is the table the SQL/MCP flow
actually uses (domain_config.yaml table_name / mcp dormant_risk.py TABLE).

Relationship types:
  - co_borrower    : shared loan / joint policy (has_loan=True customers)
  - guarantor      : one customer guarantees another's loan
  - same_employer  : work at the same company (proxy: same occupation_category + city)
  - same_branch    : registered at the same branch_code

Output: customer_relationships.csv
  customer_id | related_customer_id | relationship_type | risk_weight | is_active
"""

import csv
import random
from collections import defaultdict
from pathlib import Path

random.seed(99)

SRC = Path("/Users/trianonurhikmat/Documents/Works/cloudera/account/data intelligence/ask-data/data/sample_data_parquet/customer_dormant_segment.csv")
OUT = Path("/Users/trianonurhikmat/Documents/Works/cloudera/account/data intelligence/ask-data/data/sample_data_parquet/customer_relationships.csv")

# ── Load customers ─────────────────────────────────────────────────────────────
with open(SRC) as f:
    rows = list(csv.DictReader(f))

all_ids       = [r["customer_id"] for r in rows]
by_branch     = defaultdict(list)
by_occ_city   = defaultdict(list)
has_loan_ids  = []
high_risk     = []

for r in rows:
    by_branch[r["branch_code"]].append(r["customer_id"])
    by_occ_city[(r["occupation_category"], r["city"])].append(r["customer_id"])
    if r["has_loan"] == "True":
        has_loan_ids.append(r["customer_id"])
    if r["churn_risk_label"] == "HIGH" or r["dormant_risk_level"] == "HIGH":
        high_risk.append(r["customer_id"])

# ── Relationship config ────────────────────────────────────────────────────────
REL_CONFIGS = {
    "co_borrower":   {"weight_range": (0.70, 0.95), "count": 900},
    "guarantor":     {"weight_range": (0.80, 0.99), "count": 700},
    "same_employer": {"weight_range": (0.30, 0.60), "count": 1400},
    "same_branch":   {"weight_range": (0.10, 0.35), "count": 1800},
}

edges = set()
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
        "is_active":           random.choice(["true", "true", "true", "false"]),
    })
    return True

# ── co_borrower: high-risk customers with active loans, paired with other loan holders ──
cfg = REL_CONFIGS["co_borrower"]
attempts = 0
pool = has_loan_ids or all_ids
while len([r for r in results if r["relationship_type"] == "co_borrower"]) < cfg["count"] and attempts < 15000:
    a = random.choice(high_risk) if high_risk and random.random() < 0.5 else random.choice(pool)
    b = random.choice(pool)
    w = random.uniform(*cfg["weight_range"])
    add_edge(a, b, "co_borrower", w)
    attempts += 1

# ── guarantor: high-risk borrowers guaranteed by other loan-holding customers ──────
cfg = REL_CONFIGS["guarantor"]
attempts = 0
while len([r for r in results if r["relationship_type"] == "guarantor"]) < cfg["count"] and attempts < 15000:
    debtor    = random.choice(high_risk) if high_risk else random.choice(all_ids)
    guarantor = random.choice(pool)
    w = random.uniform(*cfg["weight_range"])
    add_edge(debtor, guarantor, "guarantor", w)
    attempts += 1

# ── same_employer: cluster by (occupation_category, city) as employer proxy ───────
cfg = REL_CONFIGS["same_employer"]
attempts = 0
occ_keys = [k for k, v in by_occ_city.items() if len(v) >= 2]
while len([r for r in results if r["relationship_type"] == "same_employer"]) < cfg["count"] and attempts < 25000:
    key = random.choice(occ_keys)
    group = by_occ_city[key]
    a, b = random.sample(group, 2)
    w = random.uniform(*cfg["weight_range"])
    add_edge(a, b, "same_employer", w)
    attempts += 1

# ── same_branch: wider regional cluster by branch_code ─────────────────────────────
cfg = REL_CONFIGS["same_branch"]
attempts = 0
branch_keys = [k for k, v in by_branch.items() if len(v) >= 2]
while len([r for r in results if r["relationship_type"] == "same_branch"]) < cfg["count"] and attempts < 25000:
    branch = random.choice(branch_keys)
    group = by_branch[branch]
    a, b = random.sample(group, 2)
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
active_counts = Counter(r["customer_id"] for r in results if r["is_active"] == "true")
active_counts.update(Counter(r["related_customer_id"] for r in results if r["is_active"] == "true"))

print(f"Total edges   : {len(results)}")
print(f"By type       : {dict(type_counts)}")
print(f"Unique pairs  : {len(edges)}")
print(f"Output        : {OUT}")
print()
print("Top 10 most-connected customers (active edges):")
for cid, count in active_counts.most_common(10):
    print(f"  {cid}: {count} active connections")
