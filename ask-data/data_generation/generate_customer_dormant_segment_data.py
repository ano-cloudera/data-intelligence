#!/usr/bin/env python3
"""
Generate synthetic Bank XYZ customer_dormant_segment sample data.

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

# Indonesia-wide cities with approximate lat/lng
CITIES = [
    # Jawa Timur
    ("Surabaya", ["Cabang Basuki Rahmat", "Cabang Darmo", "Cabang Manyar"], -7.2575, 112.7521),
    ("Malang", ["Cabang Malang Kawi", "Cabang Malang Soekarno Hatta"], -7.9797, 112.6304),
    ("Sidoarjo", ["Cabang Sidoarjo", "Cabang Waru"], -7.4478, 112.7183),
    ("Kediri", ["Cabang Kediri"], -7.8166, 112.0115),
    ("Madiun", ["Cabang Madiun"], -7.6298, 111.5239),
    ("Jember", ["Cabang Jember"], -8.1845, 113.6683),
    ("Banyuwangi", ["Cabang Banyuwangi"], -8.2191, 114.3691),
    ("Gresik", ["Cabang Gresik"], -7.1567, 112.6522),
    ("Pasuruan", ["Cabang Pasuruan"], -7.6451, 112.9079),
    ("Bojonegoro", ["Cabang Bojonegoro"], -7.1550, 111.8815),
    # DKI Jakarta
    ("Jakarta Pusat", ["Cabang Jakarta Pusat", "Cabang Gambir"], -6.1805, 106.8284),
    ("Jakarta Selatan", ["Cabang Jakarta Selatan", "Cabang Sudirman"], -6.2615, 106.8106),
    ("Jakarta Barat", ["Cabang Jakarta Barat"], -6.1481, 106.7477),
    # Jawa Barat
    ("Bandung", ["Cabang Bandung Dago", "Cabang Bandung Braga"], -6.9175, 107.6191),
    ("Bekasi", ["Cabang Bekasi", "Cabang Bekasi Barat"], -6.2383, 106.9756),
    ("Bogor", ["Cabang Bogor Sudirman"], -6.5971, 106.8060),
    ("Depok", ["Cabang Depok"], -6.4025, 106.7942),
    ("Tangerang", ["Cabang Tangerang"], -6.1784, 106.6319),
    # Jawa Tengah
    ("Semarang", ["Cabang Semarang Pemuda", "Cabang Semarang Siliwangi"], -6.9932, 110.4203),
    ("Solo", ["Cabang Solo Slamet Riyadi"], -7.5755, 110.8243),
    ("Yogyakarta", ["Cabang Yogyakarta Malioboro"], -7.7972, 110.3688),
    # Sumatera
    ("Medan", ["Cabang Medan Sudirman", "Cabang Medan Gatsu"], 3.5952, 98.6722),
    ("Palembang", ["Cabang Palembang"], -2.9761, 104.7754),
    ("Pekanbaru", ["Cabang Pekanbaru"], 0.5071, 101.4478),
    ("Padang", ["Cabang Padang"], -0.9198, 100.3531),
    ("Batam", ["Cabang Batam"], 1.1301, 104.0529),
    ("Banda Aceh", ["Cabang Banda Aceh"], 5.5483, 95.3238),
    # Kalimantan
    ("Balikpapan", ["Cabang Balikpapan"], -1.2654, 116.8312),
    ("Samarinda", ["Cabang Samarinda"], -0.5022, 117.1536),
    ("Banjarmasin", ["Cabang Banjarmasin"], -3.3186, 114.5944),
    ("Pontianak", ["Cabang Pontianak"], -0.0263, 109.3425),
    # Sulawesi
    ("Makassar", ["Cabang Makassar Sudirman", "Cabang Makassar Urip"], -5.1477, 119.4327),
    ("Manado", ["Cabang Manado"], 1.4748, 124.8421),
    ("Kendari", ["Cabang Kendari"], -3.9985, 122.5127),
    # Bali & Nusa Tenggara
    ("Denpasar", ["Cabang Denpasar Gajah Mada", "Cabang Kuta"], -8.6705, 115.2126),
    ("Mataram", ["Cabang Mataram"], -8.5833, 116.1167),
    # Papua
    ("Jayapura", ["Cabang Jayapura"], -2.5916, 140.6690),
    ("Sorong", ["Cabang Sorong"], -0.8833, 131.2500),
    # Maluku
    ("Ambon", ["Cabang Ambon"], -3.6954, 128.1814),
]

AGE_BANDS = ["18-25", "26-35", "36-45", "46-55", "56-65", ">65"]
GENDERS = ["M", "F"]
OCCUPATIONS = ["Pegawai", "Wiraswasta", "Pensiunan", "Profesional", "Pelajar", "Petani/Nelayan", "UMKM"]
INCOME_BANDS = ["<5jt", "5-10jt", "10-25jt", "25-50jt", ">50jt"]
CUSTOMER_TYPES = ["Individual", "SME"]
CAMPAIGNS = ["Reaktivasi Dormant", "Cross-sell Deposito", "Upgrade Digital Banking", "Loan Restructure Outreach", "Payroll Bundle", "SME Advisory"]
CHANNELS = ["Mobile Banking", "Relationship Manager", "Branch Outreach", "SMS Campaign", "Call Center"]
REASON_CODES = ["LOW_ACTIVITY", "NO_DIGITAL_LOGIN", "BALANCE_DECLINE", "MATURED_DEPOSIT", "LOW_TRANSACTION_COUNT", "NORMAL_ACTIVITY"]

LOAN_TYPES = ["KPR", "KKB", "KTA", "None"]
DIGITAL_ADOPTION_LEVELS = ["Active", "Passive", "None"]


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


def credit_risk_label(score):
    if score >= 750:
        return "GOOD"
    if score >= 650:
        return "FAIR"
    if score >= 550:
        return "POOR"
    return "BAD"


def generate_row(i, snapshot_date):
    segment, desc = choose_segment()
    city_entry = random.choice(CITIES)
    city, branches, base_lat, base_lng = city_entry
    branch = random.choice(branches)

    # Add small jitter to lat/lng so points don't stack exactly
    lat = round(base_lat + random.uniform(-0.05, 0.05), 6)
    lng = round(base_lng + random.uniform(-0.05, 0.05), 6)

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

    # Credit score: 300-850, higher for affluent/payroll, lower for dormant/bad credit
    if is_affluent:
        base_credit = random.randint(700, 850)
    elif is_dormant_segment:
        base_credit = random.randint(300, 550)
    elif is_credit:
        base_credit = random.randint(450, 680)
    elif is_payroll:
        base_credit = random.randint(620, 800)
    else:
        base_credit = random.randint(500, 750)
    score = base_credit

    # Churn probability: correlated with dormant_probability but not identical
    churn_base = dormant_probability * 0.70 + random.uniform(-0.05, 0.15)
    if is_dormant_segment:
        churn_base += 0.15
    if is_digital:
        churn_base -= 0.10
    churn_prob = round(clamp(churn_base), 4)

    churn_label = "HIGH" if churn_prob >= 0.65 else ("MEDIUM" if churn_prob >= 0.35 else "LOW")

    # Loan type
    if has_loan:
        if is_sme:
            loan_type = "KTA"
        elif loan > 500_000_000:
            loan_type = random.choice(["KPR", "KKB"])
        else:
            loan_type = random.choice(LOAN_TYPES[:-1])
    else:
        loan_type = "None"

    # Digital banking adoption
    if is_digital or (has_mobile and digital_login_count >= 20):
        digital_adoption = "Active"
    elif has_mobile or has_internet:
        digital_adoption = "Passive"
    else:
        digital_adoption = "None"

    return {
        "customer_id": f"CUST{i:09d}",
        "snapshot_date": snapshot_date.isoformat(),
        "age_band": random.choice(AGE_BANDS),
        "gender": random.choice(GENDERS),
        "city": city,
        "district": city,
        "branch_code": f"BXY{random.randint(100, 999)}",
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
        # New columns
        "credit_score": score,
        "credit_risk_label": credit_risk_label(score),
        "churn_probability": churn_prob,
        "churn_risk_label": churn_label,
        "loan_type": loan_type,
        "digital_banking_adoption": digital_adoption,
        "lat": lat,
        "lng": lng,
        "segmentation_model_version": "segmentation-kmeans-v2",
        "dormant_model_version": "dormant-xgboost-v2",
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
