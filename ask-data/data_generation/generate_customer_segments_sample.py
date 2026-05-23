"""
Generate 10.000 sample rows dari customer_segments.parquet dengan status_rekening variatif.

Distribusi status:
  70% Aktif   (status_rekening=0)
  20% Dormant (status_rekening=1)
  10% Tutup   (status_rekening=2)

Kolom turunan disesuaikan agar konsisten dengan status baru:
  - status_label, hari_sejak_trx, activity_level, rfm_r, rfm_score, rfm_segment

Output: data/sample_data_parquet/customer_segments_sample_10k.parquet
"""
from __future__ import annotations

import random
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path

RANDOM_SEED = 42
SAMPLE_SIZE = 1_000
DIST = {0: 0.70, 1: 0.20, 2: 0.10}  # status_rekening distribution

INPUT  = Path(__file__).parents[1] / "data/sample_data_parquet/customer_segments.parquet"
OUTPUT = Path(__file__).parents[1] / "data/sample_data_parquet/customer_segments_sample_1k.parquet"

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)


def assign_status(n: int) -> np.ndarray:
    statuses = np.array(
        [0] * int(n * DIST[0]) +
        [1] * int(n * DIST[1]) +
        [2] * (n - int(n * DIST[0]) - int(n * DIST[1]))
    )
    np.random.shuffle(statuses)
    return statuses


def hari_sejak_trx_for_status(status: int) -> int:
    if status == 0:   # Aktif
        return random.randint(1, 30)
    elif status == 1:  # Dormant
        return random.randint(31, 365)
    else:              # Tutup
        return random.randint(366, 730)


def activity_level_for_hari(hari: int) -> str:
    if hari <= 7:
        return "Sangat Aktif (≤7 hari)"
    elif hari <= 30:
        return "Aktif (8-30 hari)"
    elif hari <= 180:
        return "Kurang Aktif (31-180 hari)"
    else:
        return "Tidak Aktif (>180 hari)"


def rfm_r_for_status(status: int) -> int:
    if status == 0:
        return random.randint(4, 5)
    elif status == 1:
        return random.randint(2, 3)
    else:
        return 1


def rfm_segment_for_score(score: int) -> str:
    if score >= 13:
        return "Champions"
    elif score >= 10:
        return "Loyal"
    elif score >= 7:
        return "Potential"
    elif score >= 5:
        return "At Risk"
    else:
        return "Lost"


def main():
    print(f"Reading {INPUT}...")
    df = pd.read_parquet(INPUT)
    print(f"Source: {len(df):,} rows, {len(df.columns)} columns")

    # Stratified sample by cluster_label — use index to avoid group-key drop in newer pandas
    idx = (
        df.groupby("cluster_label", group_keys=False)
        .apply(lambda x: x.sample(frac=SAMPLE_SIZE / len(df), random_state=RANDOM_SEED))
        .index
    )
    sample = df.loc[idx].sample(n=min(SAMPLE_SIZE, len(idx)), random_state=RANDOM_SEED).reset_index(drop=True)
    print(f"Sampled: {len(sample):,} rows")

    # Assign new status_rekening
    sample["status_rekening"] = assign_status(len(sample))

    # Update derived columns
    sample["status_label"] = sample["status_rekening"].map({0: "Aktif", 1: "Dormant", 2: "Tutup"})
    sample["hari_sejak_trx"] = sample["status_rekening"].apply(hari_sejak_trx_for_status)
    sample["activity_level"] = sample["hari_sejak_trx"].apply(activity_level_for_hari)
    sample["rfm_r"] = sample["status_rekening"].apply(rfm_r_for_status)
    sample["rfm_score"] = sample["rfm_r"] + sample["rfm_f"] + sample["rfm_m"]
    sample["rfm_segment"] = sample["rfm_score"].apply(rfm_segment_for_score)

    # Cast numeric types to match Impala DDL exactly
    sample["status_rekening"] = sample["status_rekening"].astype("int8")
    sample["total_tx"]        = sample["total_tx"].astype("int64")
    sample["hari_sejak_trx"]  = sample["hari_sejak_trx"].astype("int64")
    sample["cluster_kmeans"]  = sample["cluster_kmeans"].astype("int64")
    sample["cluster_gmm"]     = sample["cluster_gmm"].astype("int64")
    sample["rfm_r"]           = sample["rfm_r"].astype("int64")
    sample["rfm_f"]           = sample["rfm_f"].astype("int64")
    sample["rfm_m"]           = sample["rfm_m"].astype("int64")
    sample["rfm_score"]       = sample["rfm_score"].astype("int64")
    sample["umur"]            = sample["umur"].astype("int32")
    sample["saldo_t0"]        = sample["saldo_t0"].astype("float64")
    sample["rasio_kredit"]    = sample["rasio_kredit"].astype("float64")
    sample["gmm_max_prob"]    = sample["gmm_max_prob"].astype("float64")
    sample["gmm_entropy"]     = sample["gmm_entropy"].astype("float64")
    for col in ["gmm_p0","gmm_p1","gmm_p2","gmm_p3","gmm_p4","gmm_p5","gmm_p6","gmm_p7"]:
        sample[col] = sample[col].astype("float64")

    # Convert t0 to string YYYY-MM-DD
    sample["t0"] = pd.to_datetime(sample["t0"]).dt.strftime("%Y-%m-%d")

    # Cast all string cols to plain Python str (avoid ArrowStringArray / large_string)
    str_cols = sample.select_dtypes(include=["object", "string"]).columns.tolist()
    for col in str_cols:
        sample[col] = sample[col].astype(str)

    # Build explicit pyarrow schema — forces pa.string() not pa.large_string()
    pa_schema = pa.schema([
        pa.field("cif",                pa.string()),
        pa.field("no_rekening",        pa.string()),
        pa.field("jenis",              pa.string()),
        pa.field("jenis_rekening",     pa.string()),
        pa.field("cabang",             pa.string()),
        pa.field("saldo_t0",           pa.float64()),
        pa.field("total_tx",           pa.int64()),
        pa.field("status_rekening",    pa.int8()),
        pa.field("status_label",       pa.string()),
        pa.field("t0",                 pa.string()),
        pa.field("umur",               pa.int32()),
        pa.field("jenis_kelamin",      pa.string()),
        pa.field("hari_sejak_trx",     pa.int64()),
        pa.field("rasio_kredit",       pa.float64()),
        pa.field("cluster_kmeans",     pa.int64()),
        pa.field("cluster_gmm",        pa.int64()),
        pa.field("gmm_max_prob",       pa.float64()),
        pa.field("gmm_entropy",        pa.float64()),
        pa.field("gmm_p0",             pa.float64()),
        pa.field("gmm_p1",             pa.float64()),
        pa.field("gmm_p2",             pa.float64()),
        pa.field("gmm_p3",             pa.float64()),
        pa.field("gmm_p4",             pa.float64()),
        pa.field("gmm_p5",             pa.float64()),
        pa.field("gmm_p6",             pa.float64()),
        pa.field("gmm_p7",             pa.float64()),
        pa.field("cluster_label",      pa.string()),
        pa.field("cluster_color",      pa.string()),
        pa.field("age_group",          pa.string()),
        pa.field("jenis_kelamin_label",pa.string()),
        pa.field("saldo_segment",      pa.string()),
        pa.field("activity_level",     pa.string()),
        pa.field("rfm_r",              pa.int64()),
        pa.field("rfm_f",              pa.int64()),
        pa.field("rfm_m",              pa.int64()),
        pa.field("rfm_score",          pa.int64()),
        pa.field("rfm_segment",        pa.string()),
    ])

    # Write via pyarrow with explicit schema
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pandas(sample, schema=pa_schema, preserve_index=False)
    pq.write_table(table, OUTPUT)
    size_mb = OUTPUT.stat().st_size / 1024 / 1024
    print(f"\nOutput: {OUTPUT}")
    print(f"Size  : {size_mb:.1f} MB")
    print(f"Rows  : {len(sample):,}")

    print("\n=== Distribusi Status ===")
    print(sample.groupby(["status_rekening", "status_label"]).size().reset_index(name="count").to_string(index=False))

    for col in ["cluster_label", "rfm_segment", "activity_level"]:
        if col in sample.columns:
            print(f"\n=== Distribusi {col} ===")
            print(sample.groupby(col).size().reset_index(name="count").to_string(index=False))

    print("\nDone! Upload file ini ke S3:")
    print(f"  s3a://go01-demo/user/cai-demo-se-indonesia/data/customer_segments/")
    print("\nLalu jalankan di Hue:")
    print("  COMPUTE STATS cai_sdx_se_indonesia.customer_segments_staging;")


if __name__ == "__main__":
    main()
