#!/usr/bin/env python3
"""
Generate synthetic Bank Jawa Timur customer_dormant_segment sample data.

No real PII is generated.
customer_id is synthetic analytics identifier only.
"""

import argparse
import csv
import random
from datetime import date, datetime, timedelta
from pathlib import Path


SEGMENTS = [
    ("Affluent Depositor", "Nasabah saldo tinggi dengan kepemilikan deposito kuat"),
    ("Mass Retail", "Nasabah retail umum dengan transaksi reguler"),
    ("Digital Active", "Nasabah aktif di channel digital"),
    ("Credit Heavy", "Nasabah dengan eksposur pinjaman tinggi"),
    ("Dormant Risk", "Nasabah dengan aktivitas rendah dan risiko dormant"),
    ("Payroll Customer", "Nasabah payroll aktif"),
    ("SME Owner", "Nasabah pemilik usaha kecil dan menengah"),
]

CITIES = [
    ("Surabaya", ["Cabang Basuki Rahmat", "Cabang Darmo", "Cabang Manyar"]),
    ("Malang", ["Cabang Malang Kawi", "Cabang Malang Soekarno Hatta"]),
    ("Sidoarjo", ["Cabang Sidoarjo", "Cabang Waru"]),
    ("Kediri", ["Cabang Kediri"]),
    ("Madiun", ["Cabang Madiun"]),
    ("Jember", ["Cabang Jember"]),
    ("Banyuwangi", ["Cabang Banyuwangi"]),
    ("Gresik", ["Cabang Gresik"]),
    ("Pasuruan", ["Cabang Pasuruan"]),
    ("Bojonegoro", ["Cabang Bojonegoro"]),
]

AGE_BANDS = ["18-25", "26-35", "36-45", "46-55", "56-65", ">65"]
GENDERS = ["M", "F"]
OCCUPATIONS = ["Pegawai", "Wiraswasta", "Pensiunan", "Profesional", "Pelajar", "Petani/Nelayan", "UMKM"]
INCOME_BANDS = ["<5jt", "5-10jt", "10-25jt", "25-50jt", ">50jt"]
CUSTOMER_TYPES = ["Individual", "SME"]
CAMPAIGNS = ["Reaktivasi Dormant", "Cross-sell Deposito", "Upgrade Digital Banking", "Loan Restructure Outreach", "Payroll Bundle", "SME Advisory"]
CHANNELS = ["Mobile Banking", "Relationship Manager", "Branch Outreach", "SMS Campaign", "Call Center"]
REASON_CODES = ["LOW_ACTIVITY", "NO_DIGITAL_LOGIN", "BALANCE_DECLINE", "MATURED_DEPOSIT", "LOW_TRANSACTION_COUNT", "NORMAL_ACTIVITY"]


def money(min_v, max_v):
    return round(random.uniform(min_v, max_v), 2)


def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def choose_segment():
    weights = [0.08, 0.34, 0.18, 0.10, 0.14, 0.10, 0.06]
    return random.choices(SEGMENTS, weights=weights, k=1)[0]


def dormant_level(prob):
    if prob >= 0.70:
        return "HIGH"
    if prob >= 0.40:
        return "MEDIUM"
    return "LOW"


def generate_row(i, snapshot_date):
    segment, desc = choose_segment()
    city, branches = random.choice(CITIES)
    branch = random.choice(branches)

    is_digital = segment == "Digital Active"
    is_affluent = segment == "Affluent Depositor"
    is_credit = segment == "Credit Heavy"
    is_dormant_segment = segment == "Dormant Risk"
    is_payroll = segment == "Payroll Customer"
    is_sme = segment == "SME Owner"

    days_since_last_txn = random.randint(0, 25)
    if is_dormant_segment:
        days_since_last_txn = random.randint(80, 360)
    elif random.random() < 0.08:
        days_since_last_txn = random.randint(45, 180)

    monthly_txn_count = random.randint(5, 80)
    if is_digital:
        monthly_txn_count = random.randint(40, 180)
    if is_dormant_segment:
        monthly_txn_count = random.randint(0, 8)

    digital_login_count = random.randint(0, 20)
    if is_digital:
        digital_login_count = random.randint(30, 200)
    if is_dormant_segment:
        digital_login_count = random.randint(0, 3)

    active_months = random.randint(3, 6)
    if is_dormant_segment:
        active_months = random.randint(0, 2)

    savings = money(500_000, 35_000_000)
    deposit = money(0, 75_000_000)
    loan = money(0, 100_000_000)

    if is_affluent:
        savings = money(50_000_000, 500_000_000)
        deposit = money(100_000_000, 2_000_000_000)
    if is_credit:
        loan = money(150_000_000, 2_500_000_000)
    if is_sme:
        savings = money(20_000_000, 300_000_000)
        loan = money(100_000_000, 1_500_000_000)
    if is_dormant_segment:
        savings *= random.uniform(0.1, 0.6)
        deposit *= random.uniform(0.0, 0.5)

    base_prob = (days_since_last_txn / 360.0) * 0.55
    base_prob += max(0, (6 - active_months)) * 0.05
    base_prob += 0.20 if monthly_txn_count <= 5 else 0
    base_prob += 0.10 if digital_login_count <= 2 else 0
    base_prob += random.uniform(-0.05, 0.07)
    dormant_probability = round(clamp(base_prob), 4)

    risk = dormant_level(dormant_probability)
    dormant_flag = dormant_probability >= 0.70

    if risk == "HIGH":
        campaign = "Reaktivasi Dormant"
        channel = random.choice(["Branch Outreach", "Call Center", "SMS Campaign"])
        action = "Hubungi nasabah untuk reaktivasi transaksi dan penawaran campaign personal."
        reason = random.choice(["LOW_ACTIVITY", "NO_DIGITAL_LOGIN", "LOW_TRANSACTION_COUNT"])
    elif segment == "Affluent Depositor":
        campaign = "Cross-sell Deposito"
        channel = random.choice(["Relationship Manager", "Branch Outreach"])
        action = "Tawarkan produk deposito atau wealth bundling sesuai profil saldo."
        reason = "NORMAL_ACTIVITY"
    elif is_digital:
        campaign = "Upgrade Digital Banking"
        channel = "Mobile Banking"
        action = "Dorong penggunaan fitur digital dan transaksi rutin."
        reason = "NORMAL_ACTIVITY"
    else:
        campaign = random.choice(CAMPAIGNS)
        channel = random.choice(CHANNELS)
        action = "Lakukan engagement sesuai segmentasi dan perilaku transaksi."
        reason = random.choice(REASON_CODES)

    has_deposit = deposit > 5_000_000
    has_loan = loan > 10_000_000
    has_mobile = is_digital or random.random() < 0.55
    has_internet = has_mobile and random.random() < 0.60

    return {
        "customer_id": f"CUST{i:09d}",
        "snapshot_date": snapshot_date.isoformat(),
        "age_band": random.choice(AGE_BANDS),
        "gender": random.choice(GENDERS),
        "city": city,
        "district": city,
        "branch_code": f"BJTM{random.randint(100, 999)}",
        "branch_name": branch,
        "customer_tenure_months": random.randint(3, 240),
        "occupation_category": "UMKM" if is_sme else random.choice(OCCUPATIONS),
        "income_band": random.choice(INCOME_BANDS),
        "customer_type": "SME" if is_sme else random.choice(CUSTOMER_TYPES),
        "total_accounts": random.randint(1, 6),
        "has_savings": True,
        "has_current_account": is_sme or random.random() < 0.15,
        "has_deposit": has_deposit,
        "has_loan": has_loan,
        "has_mobile_banking": has_mobile,
        "has_internet_banking": has_internet,
        "product_holding_count": random.randint(1, 5),
        "avg_savings_balance_3m": round(savings, 2),
        "avg_deposit_balance_3m": round(deposit * random.uniform(0.8, 1.05), 2),
        "total_deposit_balance": round(deposit, 2),
        "outstanding_loan_balance": round(loan, 2),
        "monthly_avg_transaction_amount": money(50_000, 15_000_000),
        "monthly_transaction_count": monthly_txn_count,
        "days_since_last_transaction": days_since_last_txn,
        "active_months_last_6m": active_months,
        "debit_transaction_count_3m": random.randint(0, monthly_txn_count * 3),
        "credit_transaction_count_3m": random.randint(0, monthly_txn_count * 3),
        "digital_login_count_3m": digital_login_count,
        "atm_transaction_count_3m": random.randint(0, 60),
        "branch_transaction_count_3m": random.randint(0, 12),
        "customer_segment": segment,
        "segment_description": desc,
        "segment_score": round(random.uniform(0.55, 0.98), 4),
        "dormant_flag": dormant_flag,
        "dormant_risk_level": risk,
        "dormant_probability": dormant_probability,
        "dormant_reason_code": reason,
        "recommended_campaign": campaign,
        "recommended_channel": channel,
        "next_best_action": action,
        "segmentation_model_version": "segmentation-kmeans-v1",
        "dormant_model_version": "dormant-xgboost-v1",
        "scoring_timestamp": datetime.now().replace(microsecond=0).isoformat(sep=" "),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=10000)
    parser.add_argument("--output-dir", default="data")
    args = parser.parse_args()

    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    snapshot_date = date.today().replace(day=1)
    rows = [generate_row(i + 1, snapshot_date) for i in range(args.rows)]

    csv_path = outdir / "customer_dormant_segment.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows):,} rows to {csv_path}")


if __name__ == "__main__":
    main()
