#!/usr/bin/env python3
"""
Upload customer_segments_extended.parquet ke Impala sebagai customer_segments_staging.

Cara pakai:
  python3 upload_to_impala.py [--table customer_segments_staging] [--db cai_sdx_se_indonesia]

Prasyarat (install dulu jika belum):
  pip install impala impyla pyarrow pandas

Kredensial diambil dari environment variables atau .env file di ../ask-data/.env
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

# Coba load dari .env
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parents[1] / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"Loaded env from {env_path}")
except ImportError:
    pass

IMPALA_HOST      = os.getenv("IMPALA_HOST",      "coordinator-default-impala-aws.dw-go01-demo-aws.ylcu-atmi.cloudera.site")
IMPALA_PORT      = int(os.getenv("IMPALA_PORT",  "443"))
IMPALA_HTTP_PATH = os.getenv("IMPALA_HTTP_PATH", "cliservice")
CDP_USER         = os.getenv("CDP_USER",         "triano")
CDP_PASS         = os.getenv("CDP_PASS",         "")
DB_NAME          = os.getenv("DB_NAME",          "cai_sdx_se_indonesia")


def get_impala_conn():
    from impala.dbapi import connect
    return connect(
        host=IMPALA_HOST,
        port=IMPALA_PORT,
        database=DB_NAME,
        auth_mechanism="LDAP",
        use_ssl=True,
        user=CDP_USER,
        password=CDP_PASS,
        http_path=IMPALA_HTTP_PATH,
    )


PARQUET_TYPE_MAP = {
    "int8":    "TINYINT",
    "int16":   "SMALLINT",
    "int32":   "INT",
    "int64":   "BIGINT",
    "float32": "FLOAT",
    "float64": "DOUBLE",
    "bool":    "BOOLEAN",
    "object":  "STRING",
    "string":  "STRING",
}


def pandas_dtype_to_impala(dtype) -> str:
    dt = str(dtype)
    if "int8"   in dt: return "TINYINT"
    if "int16"  in dt: return "SMALLINT"
    if "int32"  in dt: return "INT"
    if "int64"  in dt: return "BIGINT"
    if "float32" in dt: return "FLOAT"
    if "float64" in dt: return "DOUBLE"
    if "bool"   in dt: return "BOOLEAN"
    if "datetime" in dt: return "TIMESTAMP"
    return "STRING"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--table", default="customer_segments_staging")
    parser.add_argument("--db",    default=DB_NAME)
    parser.add_argument("--parquet", default=str(
        Path(__file__).parents[1] / "data/sample_data_parquet/customer_segments_extended.parquet"
    ))
    parser.add_argument("--chunk-size", type=int, default=5000, help="Rows per INSERT batch")
    parser.add_argument("--recreate", action="store_true", help="DROP TABLE IF EXISTS before create")
    args = parser.parse_args()

    import pyarrow.parquet as pq
    import pandas as pd

    print(f"Reading {args.parquet} ...")
    df = pq.read_table(args.parquet).to_pandas()
    print(f"  {len(df):,} rows × {len(df.columns)} columns")

    col_defs = ", ".join(f"`{c}` {pandas_dtype_to_impala(df[c].dtype)}" for c in df.columns)

    print(f"\nConnecting to Impala at {IMPALA_HOST}:{IMPALA_PORT} ...")
    conn = get_impala_conn()
    cur  = conn.cursor()

    cur.execute(f"USE `{args.db}`")

    if args.recreate:
        print(f"Dropping {args.table} ...")
        cur.execute(f"DROP TABLE IF EXISTS `{args.table}`")

    print(f"Creating {args.table} if not exists ...")
    cur.execute(f"CREATE TABLE IF NOT EXISTS `{args.table}` ({col_defs}) STORED AS PARQUET")

    print(f"Truncating {args.table} ...")
    cur.execute(f"TRUNCATE TABLE `{args.table}`")

    total = len(df)
    inserted = 0
    print(f"Inserting {total:,} rows in chunks of {args.chunk_size} ...")

    for start in range(0, total, args.chunk_size):
        chunk = df.iloc[start: start + args.chunk_size]
        rows  = []
        for _, row in chunk.iterrows():
            vals = []
            for col in df.columns:
                v = row[col]
                if pd.isna(v):
                    vals.append("NULL")
                elif isinstance(v, str):
                    v2 = v.replace("'", "\\'")
                    vals.append(f"'{v2}'")
                elif isinstance(v, bool):
                    vals.append("TRUE" if v else "FALSE")
                else:
                    vals.append(str(v))
            rows.append(f"({', '.join(vals)})")
        sql = f"INSERT INTO `{args.table}` VALUES {', '.join(rows)}"
        cur.execute(sql)
        inserted += len(chunk)
        print(f"  {inserted:,}/{total:,} rows inserted", end="\r")

    print(f"\nDone. {inserted:,} rows inserted into {args.db}.{args.table}")
    cur.execute(f"COMPUTE STATS `{args.table}`")
    print("COMPUTE STATS done.")
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
