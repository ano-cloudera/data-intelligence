"""
Generate customer_relationships.csv — synthetic graph edges for risk propagation demo.

Aligned to customer_segments_staging (cif format) — the table domain_config.yaml
actually points to (table_name: customer_segments_staging), which carries
credit_score/credit_risk_label/churn_probability/churn_risk_label/lat/lng.
Using this table (instead of customer_dormant_segment) lets the risk graph
demo also surface map + credit-risk fields on the same customer records.

Relationship types:
  - co_borrower    : shared loan / joint policy (customers with loan_type != None)
  - guarantor      : one customer guarantees another's loan
  - same_employer  : proxy — same cabang + similar age_group
  - same_branch    : same cabang_name

Demo requirement: a natural "top N churn/credit risk" SQL query must land on
customers that ALSO have a rich risk network — otherwise the graph follow-up
in a live demo can hit a customer with zero connections. To guarantee this,
the highest-risk customers (by churn_probability) are seeded with a
guaranteed minimum number of active edges FIRST, before the random fill.

Output: customer_relationships.csv
  customer_id | related_customer_id | relationship_type | risk_weight | is_active
"""

import random
from collections import defaultdict
from pathlib import Path

import pandas as pd

random.seed(99)

SRC = Path("/Users/trianonurhikmat/Documents/Works/cloudera/account/data intelligence/ask-data/data/sample_data_parquet/customer_segments_staging_10k.parquet")
OUT = Path("/Users/trianonurhikmat/Documents/Works/cloudera/account/data intelligence/ask-data/data/sample_data_parquet/customer_relationships.csv")

# ── Load customers ─────────────────────────────────────────────────────────────
df = pd.read_parquet(SRC)
df = df.drop_duplicates(subset="cif", keep="first").reset_index(drop=True)

all_ids       = df["cif"].tolist()
by_branch     = defaultdict(list)
by_branch_age = defaultdict(list)
loan_ids      = []
high_risk     = []

for _, r in df.iterrows():
    by_branch[r["cabang_name"]].append(r["cif"])
    by_branch_age[(r["cabang_name"], r["age_group"])].append(r["cif"])
    if r["loan_type"] and r["loan_type"] != "None":
        loan_ids.append(r["cif"])
    if r["churn_risk_label"] == "HIGH" or r["credit_risk_label"] == "BAD":
        high_risk.append(r["cif"])

# Top-risk customers most likely to surface in a "highest churn + credit BAD"
# demo query — guarantee each of these gets a real network below. Seeded from
# both the highest churn_probability AND the highest saldo_t0 within that
# risk group, since a demo query can reasonably sort by either.
risk_pool_df = df[(df["churn_risk_label"] == "HIGH") & (df["credit_risk_label"] == "BAD")]
by_churn = risk_pool_df.sort_values("churn_probability", ascending=False)["cif"].head(30).tolist()
by_saldo = risk_pool_df.sort_values("saldo_t0", ascending=False)["cif"].head(30).tolist()
guaranteed_network_ids = list(dict.fromkeys(by_churn + by_saldo))  # dedupe, preserve order

# ── Relationship config ────────────────────────────────────────────────────────
REL_CONFIGS = {
    "co_borrower":   {"weight_range": (0.70, 0.95), "count": 900},
    "guarantor":     {"weight_range": (0.80, 0.99), "count": 700},
    "same_employer": {"weight_range": (0.30, 0.60), "count": 1400},
    "same_branch":   {"weight_range": (0.10, 0.35), "count": 1800},
}

edges = set()
results = []

def add_edge(a, b, rel_type, weight, force_active=False):
    key = (min(a, b), max(a, b), rel_type)
    if key in edges or a == b:
        return False
    edges.add(key)
    results.append({
        "customer_id":         a,
        "related_customer_id": b,
        "relationship_type":   rel_type,
        "risk_weight":         round(weight, 3),
        "is_active":           "true" if force_active else random.choice(["true", "true", "true", "false"]),
    })
    return True

# ── Seed step: guarantee each top-risk customer gets 3-5 active connections ───────
pool_for_seed = loan_ids or all_ids
for cid in guaranteed_network_ids:
    target_edges = random.randint(3, 5)
    made = 0
    attempts = 0
    while made < target_edges and attempts < 50:
        attempts += 1
        rel_type = random.choices(
            ["co_borrower", "guarantor", "same_employer", "same_branch"],
            weights=[0.35, 0.25, 0.2, 0.2],
        )[0]
        other = random.choice(pool_for_seed if rel_type in ("co_borrower", "guarantor") else all_ids)
        if other == cid:
            continue
        lo, hi = REL_CONFIGS[rel_type]["weight_range"]
        if add_edge(cid, other, rel_type, random.uniform(lo, hi), force_active=True):
            made += 1

# ── co_borrower: high-risk customers with loans, paired with other loan holders ──
cfg = REL_CONFIGS["co_borrower"]
attempts = 0
pool = loan_ids or all_ids
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

# ── same_employer: cluster by (cabang, age_group) as employer proxy ───────────────
cfg = REL_CONFIGS["same_employer"]
attempts = 0
group_keys = [k for k, v in by_branch_age.items() if len(v) >= 2]
while len([r for r in results if r["relationship_type"] == "same_employer"]) < cfg["count"] and attempts < 25000:
    key = random.choice(group_keys)
    group = by_branch_age[key]
    a, b = random.sample(group, 2)
    w = random.uniform(*cfg["weight_range"])
    add_edge(a, b, "same_employer", w)
    attempts += 1

# ── same_branch: wider regional cluster by cabang_name ─────────────────────────────
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

out_df = pd.DataFrame(results, columns=FIELDNAMES)
out_df.to_csv(OUT, index=False)

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
print(f"Top-risk customers (churn HIGH + credit BAD, top {len(guaranteed_network_ids)} by churn_probability):")
print("  All guaranteed >= 3 active connections. Sample:")
for cid in guaranteed_network_ids[:10]:
    row = df[df["cif"] == cid].iloc[0]
    print(f"  {cid}: {active_counts.get(cid, 0)} active connections | churn={row['churn_probability']:.3f} credit={row['credit_risk_label']} saldo={row['saldo_t0']:.0f}")

print()
print("Top 10 most-connected customers overall (active edges):")
for cid, count in active_counts.most_common(10):
    row = df[df["cif"] == cid].iloc[0]
    print(f"  {cid}: {count} active connections | churn={row['churn_risk_label']} credit={row['credit_risk_label']} segment={row['cluster_label']}")
