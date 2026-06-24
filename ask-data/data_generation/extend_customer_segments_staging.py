#!/usr/bin/env python3
"""
Extend customer_segments_staging dengan kolom baru untuk Bank XYZ demo:
  - credit_score          INT     (300-850)
  - credit_risk_label     STRING  (GOOD/FAIR/POOR/BAD)
  - churn_probability     DOUBLE  (0.0-1.0)
  - churn_risk_label      STRING  (HIGH/MEDIUM/LOW)
  - loan_type             STRING  (KPR/KKB/KTA/None)
  - digital_banking_adoption STRING (Active/Passive/None)

Baca dari customer_segments.parquet (219k rows) → tambah kolom baru →
output: customer_segments_extended.parquet
"""
from __future__ import annotations

import random
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path

RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

INPUT  = Path(__file__).parents[1] / "data/sample_data_parquet/customer_segments.parquet"
OUTPUT = Path(__file__).parents[1] / "data/sample_data_parquet/customer_segments_extended.parquet"


def credit_risk_label(score: int) -> str:
    if score >= 750: return "GOOD"
    if score >= 650: return "FAIR"
    if score >= 550: return "POOR"
    return "BAD"


def churn_risk_label(prob: float) -> str:
    if prob >= 0.65: return "HIGH"
    if prob >= 0.35: return "MEDIUM"
    return "LOW"


def generate_new_columns(df: pd.DataFrame) -> pd.DataFrame:
    n = len(df)
    rng = np.random.default_rng(RANDOM_SEED)

    cluster = df["cluster_label"].fillna("").str.lower()
    status  = df["status_rekening"].fillna(0).astype(int)
    saldo   = df["saldo_t0"].fillna(0).astype(float)
    rfm     = df["rfm_segment"].fillna("").str.lower() if "rfm_segment" in df.columns else pd.Series([""] * n)

    # === credit_score ===
    base_score = rng.integers(500, 751, n)  # default 500-750

    # Affluent / Champions → higher score
    mask_good = (saldo > 10_000_000) | rfm.str.contains("champions|loyal", na=False)
    base_score = np.where(mask_good, rng.integers(680, 851, n), base_score)

    # Dormant / Lost → lower score
    mask_poor = (status == 1) | rfm.str.contains("lost|at risk", na=False)
    base_score = np.where(mask_poor, rng.integers(300, 550, n), base_score)

    # Young Syariah Digital → moderate-good
    mask_digital = cluster.str.contains("syariah|digital", na=False)
    base_score = np.where(mask_digital & ~mask_poor, rng.integers(580, 751, n), base_score)

    credit_scores = base_score.astype(int)
    credit_labels = [credit_risk_label(s) for s in credit_scores]

    # === churn_probability ===
    hari = df["hari_sejak_trx"].fillna(30).astype(float)
    base_churn = (hari / 365.0) * 0.6
    base_churn += np.where(status == 1, rng.uniform(0.15, 0.30, n), 0)
    base_churn += np.where(status == 2, rng.uniform(0.35, 0.50, n), 0)
    base_churn -= np.where(mask_digital, rng.uniform(0.05, 0.15, n), 0)
    noise = rng.uniform(-0.05, 0.10, n)
    churn_probs = np.clip(base_churn + noise, 0.0, 1.0).round(4)
    churn_labels = [churn_risk_label(p) for p in churn_probs]

    # === loan_type ===
    loan_types = []
    for i in range(n):
        r = rng.random()
        if saldo.iloc[i] > 50_000_000 and r < 0.45:
            loan_types.append("KPR")
        elif r < 0.20:
            loan_types.append("KKB")
        elif r < 0.30:
            loan_types.append("KTA")
        else:
            loan_types.append("None")

    # === digital_banking_adoption ===
    digital_adoptions = []
    for i in range(n):
        cl = cluster.iloc[i]
        r = rng.random()
        if "syariah" in cl or "digital" in cl:
            digital_adoptions.append("Active" if r < 0.80 else "Passive")
        elif "konvensional" in cl:
            digital_adoptions.append("Active" if r < 0.50 else ("Passive" if r < 0.80 else "None"))
        else:
            digital_adoptions.append("Active" if r < 0.35 else ("Passive" if r < 0.65 else "None"))

    df = df.copy()
    df["credit_score"]              = credit_scores
    df["credit_risk_label"]         = credit_labels
    df["churn_probability"]         = churn_probs
    df["churn_risk_label"]          = churn_labels
    df["loan_type"]                 = loan_types
    df["digital_banking_adoption"]  = digital_adoptions

    return df


def main():
    print(f"Reading {INPUT} ...")
    df = pq.read_table(INPUT).to_pandas()
    print(f"  {len(df):,} rows, {len(df.columns)} columns")

    df = generate_new_columns(df)
    print(f"  Extended to {len(df.columns)} columns")
    print("  New columns:", ["credit_score", "credit_risk_label", "churn_probability", "churn_risk_label", "loan_type", "digital_banking_adoption"])

    table = pa.Table.from_pandas(df, preserve_index=False)
    pq.write_table(table, OUTPUT, compression="snappy")
    print(f"Written → {OUTPUT}")
    print()
    print("Distribution check:")
    print("  credit_risk_label:", df["credit_risk_label"].value_counts().to_dict())
    print("  churn_risk_label: ", df["churn_risk_label"].value_counts().to_dict())
    print("  loan_type:        ", df["loan_type"].value_counts().to_dict())
    print("  digital_adoption: ", df["digital_banking_adoption"].value_counts().to_dict())


if __name__ == "__main__":
    main()
