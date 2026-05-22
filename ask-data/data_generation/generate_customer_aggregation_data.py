"""
Generate 100 rows of synthetic customer_aggregation data.

Usage:
    python generate_customer_aggregation_data.py [--rows 100] [--output-dir output]
"""
from __future__ import annotations

import argparse
import csv
import os
import random
from datetime import date, timedelta
from pathlib import Path


JENIS_OPTIONS = [("Perorangan", 0.80), ("Badan Usaha", 0.20)]
JENIS_REKENING_OPTIONS = [("Tabungan", 0.60), ("Giro", 0.25), ("Deposito", 0.15)]
STATUS_REKENING_OPTIONS = [(0, 0.70), (1, 0.20), (2, 0.10)]  # 0=Aktif, 1=Dormant, 2=Tutup

CABANG_LIST = [
    ("BC001", "Cabang Surabaya Utara"),
    ("BC002", "Cabang Surabaya Selatan"),
    ("BC003", "Cabang Malang"),
    ("BC004", "Cabang Sidoarjo"),
    ("BC005", "Cabang Gresik"),
    ("BC006", "Cabang Kediri"),
    ("BC007", "Cabang Madiun"),
    ("BC008", "Cabang Jember"),
    ("BC009", "Cabang Pasuruan"),
    ("BC010", "Cabang Banyuwangi"),
]

NAME_PREFIXES_PERORANGAN = ["Budi", "Siti", "Ahmad", "Dewi", "Eko", "Rina", "Hendra", "Maya", "Dian", "Agus"]
NAME_SUFFIXES = ["Santoso", "Wijaya", "Kusuma", "Pratama", "Hidayat", "Rahayu", "Susanto", "Wibowo", "Purnomo", "Hartono"]
COMPANY_PREFIXES = ["PT", "CV", "UD", "Koperasi"]
COMPANY_NAMES = ["Maju Jaya", "Sejahtera Abadi", "Karya Mandiri", "Berkah Utama", "Sumber Rezeki"]

T0_DATE = date(2024, 12, 31)


def weighted_choice(options: list[tuple]) -> object:
    items = [o[0] for o in options]
    weights = [o[1] for o in options]
    return random.choices(items, weights=weights, k=1)[0]


def generate_name(jenis: str) -> str:
    if jenis == "Perorangan":
        return f"{random.choice(NAME_PREFIXES_PERORANGAN)} {random.choice(NAME_SUFFIXES)}"
    prefix = random.choice(COMPANY_PREFIXES)
    name = random.choice(COMPANY_NAMES)
    return f"{prefix} {name}"


def generate_saldo(jenis_rekening: str, status: int) -> tuple[float, float, float]:
    if jenis_rekening == "Deposito":
        base = random.uniform(10_000_000, 500_000_000)
    elif jenis_rekening == "Giro":
        base = random.uniform(5_000_000, 200_000_000)
    else:
        base = random.uniform(500_000, 50_000_000)

    if status == 1:  # Dormant
        base *= random.uniform(0.1, 0.4)
    elif status == 2:  # Tutup
        base *= random.uniform(0.0, 0.05)

    saldo_t0 = round(base, 2)
    min_saldo = round(base * random.uniform(0.1, 0.5), 2)
    saldo_end_target = round(base * random.uniform(1.05, 1.30), 2)
    return min_saldo, saldo_t0, saldo_end_target


def generate_transactions(status: int) -> dict:
    if status == 2:  # Tutup
        total_tx = random.randint(0, 3)
    elif status == 1:  # Dormant
        total_tx = random.randint(1, 15)
    else:
        total_tx = random.randint(10, 200)

    tx_sistem = int(total_tx * random.uniform(0.1, 0.3))
    tx_nasabah = total_tx - tx_sistem

    count_kredit = random.randint(0, max(1, total_tx // 2))
    count_debit = total_tx - count_kredit

    def tx_stats(count: int, base_nominal: float) -> tuple:
        if count == 0:
            return 0.0, 0.0, 0.0, 0.0
        vals = [random.uniform(base_nominal * 0.5, base_nominal * 1.5) for _ in range(count)]
        avg = sum(vals) / len(vals)
        mn = min(vals)
        mx = max(vals)
        variance = sum((v - avg) ** 2 for v in vals) / len(vals)
        std = variance ** 0.5
        return round(avg, 2), round(mx, 2), round(mn, 2), round(std, 2)

    base = random.uniform(500_000, 10_000_000)
    avg_k, max_k, min_k, std_k = tx_stats(count_kredit, base)
    avg_d, max_d, min_d, std_d = tx_stats(count_debit, base)

    return {
        "total_tx": total_tx,
        "tx_sistem": tx_sistem,
        "tx_nasabah": tx_nasabah,
        "count_tx_kredit": count_kredit,
        "avg_nominal_kredit": avg_k,
        "max_nominal_kredit": max_k,
        "min_nominal_kredit": min_k,
        "std_nominal_kredit": std_k,
        "count_tx_debit": count_debit,
        "avg_nominal_debit": avg_d,
        "max_nominal_debit": max_d,
        "min_nominal_debit": min_d,
        "std_nominal_debit": std_d,
    }


def generate_row(i: int) -> dict:
    jenis = weighted_choice(JENIS_OPTIONS)
    jenis_rekening = weighted_choice(JENIS_REKENING_OPTIONS)
    status = weighted_choice(STATUS_REKENING_OPTIONS)
    cabang_code, cabang_name = random.choice(CABANG_LIST)

    min_saldo, saldo_t0, saldo_end_target = generate_saldo(jenis_rekening, status)
    txn = generate_transactions(status)

    days_back = random.randint(1, 365) if status != 2 else random.randint(180, 730)
    tgl_trx_terakhir = T0_DATE - timedelta(days=days_back)

    has_tx_first_6m = random.random() > 0.3 if status == 0 else random.random() > 0.7
    has_tx_last_6m = days_back <= 180

    return {
        "cif": f"CIF{i:07d}",
        "no_rekening": f"RK{i:010d}",
        "jenis": jenis,
        "name": generate_name(jenis),
        "cabang": cabang_code,
        "jenis_rekening": jenis_rekening,
        "name_cabang": cabang_name,
        "min_saldo": min_saldo,
        "saldo_t0": saldo_t0,
        "tgl_trx_terakhir": tgl_trx_terakhir.isoformat(),
        **txn,
        "has_tx_first_6m": str(has_tx_first_6m).upper(),
        "has_tx_last_6m": str(has_tx_last_6m).upper(),
        "saldo_end_target": saldo_end_target,
        "status_rekening": status,
        "t0": T0_DATE.isoformat(),
    }


FIELDNAMES = [
    "cif", "no_rekening", "jenis", "name", "cabang", "jenis_rekening", "name_cabang",
    "min_saldo", "saldo_t0", "tgl_trx_terakhir", "total_tx", "tx_sistem", "tx_nasabah",
    "count_tx_kredit", "avg_nominal_kredit", "max_nominal_kredit", "min_nominal_kredit", "std_nominal_kredit",
    "count_tx_debit", "avg_nominal_debit", "max_nominal_debit", "min_nominal_debit", "std_nominal_debit",
    "has_tx_first_6m", "has_tx_last_6m", "saldo_end_target", "status_rekening", "t0",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic customer_aggregation data")
    parser.add_argument("--rows", type=int, default=100)
    parser.add_argument("--output-dir", default="output")
    args = parser.parse_args()

    random.seed(42)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "customer_aggregation_100.csv"

    rows = [generate_row(i + 1) for i in range(args.rows)]

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {args.rows} rows → {output_file}")


if __name__ == "__main__":
    main()
