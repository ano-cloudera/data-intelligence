from __future__ import annotations

from app.impala_client import qualified_table, table_name

COLUMNS = [
    # Identitas Rekening
    ("cif",                 "STRING",    "Customer Identification"),
    ("no_rekening",         "STRING",    "Nomor rekening"),
    ("jenis",               "STRING",    "Jenis nasabah: SYARIAH / KONVEN"),
    ("jenis_rekening",      "STRING",    "Nama produk rekening, contoh: TABUNGAN IB BAROKAH"),
    ("cabang",              "STRING",    "Kode cabang, contoh: 611"),
    ("status_rekening",     "TINYINT",   "Status: 0=Aktif, 1=Dormant, 2=Tutup — tidak perlu CAST"),
    ("status_label",        "STRING",    "Label status: Aktif / Dormant / Tutup"),
    ("t0",                  "TIMESTAMP", "Reference date periode (YYYY-MM-DD)"),
    # Saldo & Transaksi
    ("saldo_t0",            "DOUBLE",    "Saldo pada periode t0 — tidak perlu CAST"),
    ("total_tx",            "BIGINT",    "Total transaksi — tidak perlu CAST"),
    ("hari_sejak_trx",      "BIGINT",    "Jumlah hari sejak transaksi terakhir — tidak perlu CAST"),
    ("rasio_kredit",        "DOUBLE",    "Rasio transaksi kredit terhadap total — tidak perlu CAST"),
    # Demografis
    ("umur",                "INT",       "Usia nasabah dalam tahun — tidak perlu CAST"),
    ("jenis_kelamin",       "STRING",    "Kode gender: P=Perempuan, L=Laki-laki"),
    ("jenis_kelamin_label", "STRING",    "Label gender: Perempuan / Laki-laki / Tidak Diketahui"),
    ("age_group",           "STRING",    "Kelompok usia: Muda (<30) / Dewasa (30-45) / Matang (45-60) / Senior (>60)"),
    # Segmentasi ML
    ("cluster_kmeans",      "BIGINT",    "Cluster K-Means: 0=Silent Mature, 1=Young Syariah Digital, 2=Konvensional Produktif"),
    ("cluster_label",       "STRING",    "Label cluster: Silent Mature / Young Syariah Digital / Konvensional Produktif"),
    ("cluster_gmm",         "BIGINT",    "Cluster GMM (0-7) — probabilistic clustering"),
    ("gmm_max_prob",        "DOUBLE",    "Probabilitas tertinggi cluster GMM"),
    ("gmm_entropy",         "DOUBLE",    "Entropy distribusi probabilitas GMM"),
    ("gmm_p0",              "DOUBLE",    "Probabilitas cluster GMM 0"),
    ("gmm_p1",              "DOUBLE",    "Probabilitas cluster GMM 1"),
    ("gmm_p2",              "DOUBLE",    "Probabilitas cluster GMM 2"),
    ("gmm_p3",              "DOUBLE",    "Probabilitas cluster GMM 3"),
    ("gmm_p4",              "DOUBLE",    "Probabilitas cluster GMM 4"),
    ("gmm_p5",              "DOUBLE",    "Probabilitas cluster GMM 5"),
    ("gmm_p6",              "DOUBLE",    "Probabilitas cluster GMM 6"),
    ("gmm_p7",              "DOUBLE",    "Probabilitas cluster GMM 7"),
    ("cluster_color",       "STRING",    "Hex color untuk visualisasi cluster"),
    # Label Segmen
    ("saldo_segment",       "STRING",    "Segmen saldo: Rendah (<1jt) / Menengah (1-10jt) / Tinggi (10-100jt) / Premium (>100jt)"),
    ("activity_level",      "STRING",    "Level aktivitas: Sangat Aktif (<=7hr) / Aktif (8-30hr) / Kurang Aktif (31-180hr) / Tidak Aktif (>180hr)"),
    # RFM Scoring
    ("rfm_r",               "BIGINT",    "RFM Recency score 1-5 (5=terbaru)"),
    ("rfm_f",               "BIGINT",    "RFM Frequency score 1-5 (5=paling sering)"),
    ("rfm_m",               "BIGINT",    "RFM Monetary score 1-5 (5=saldo tertinggi)"),
    ("rfm_score",           "BIGINT",    "Total RFM score (3-15)"),
    ("rfm_segment",         "STRING",    "Segmen RFM: Champions / Loyal / Potential / At Risk / Lost"),
]


CUSTOMER_DORMANT_SEGMENT_COLUMNS = [
    ("customer_id",                   "STRING",  "Synthetic analytics identifier (no real PII)"),
    ("snapshot_date",                 "DATE",    "Scoring snapshot date"),
    ("age_band",                      "STRING",  "Age group: 18-25, 26-35, 36-45, 46-55, 56-65, >65"),
    ("gender",                        "STRING",  "Gender: M / F"),
    ("city",                          "STRING",  "Customer city (Indonesia-wide)"),
    ("district",                      "STRING",  "Customer district"),
    ("branch_code",                   "STRING",  "Branch code"),
    ("branch_name",                   "STRING",  "Branch name"),
    ("customer_tenure_months",        "INT",     "Months since onboarding"),
    ("occupation_category",           "STRING",  "Occupation category"),
    ("income_band",                   "STRING",  "Income band: <5jt, 5-10jt, 10-25jt, 25-50jt, >50jt"),
    ("customer_type",                 "STRING",  "Individual or SME"),
    ("total_accounts",                "INT",     "Total number of accounts held"),
    ("has_savings",                   "BOOLEAN", "Has savings account"),
    ("has_deposit",                   "BOOLEAN", "Has deposit account"),
    ("has_loan",                      "BOOLEAN", "Has active loan"),
    ("has_mobile_banking",            "BOOLEAN", "Enrolled in mobile banking"),
    ("has_internet_banking",          "BOOLEAN", "Enrolled in internet banking"),
    ("product_holding_count",         "INT",     "Total products held"),
    ("avg_savings_balance_3m",        "DOUBLE",  "Average savings balance last 3 months"),
    ("avg_deposit_balance_3m",        "DOUBLE",  "Average deposit balance last 3 months"),
    ("total_deposit_balance",         "DOUBLE",  "Total current deposit balance"),
    ("outstanding_loan_balance",      "DOUBLE",  "Total outstanding loan balance"),
    ("monthly_avg_transaction_amount","DOUBLE",  "Average monthly transaction amount"),
    ("monthly_transaction_count",     "INT",     "Average monthly transaction count"),
    ("days_since_last_transaction",   "INT",     "Days since last recorded transaction"),
    ("active_months_last_6m",         "INT",     "Active months in last 6 months"),
    ("digital_login_count_3m",        "INT",     "Digital channel login count last 3 months"),
    ("customer_segment",              "STRING",  "Segment label: Affluent Depositor, Mass Retail, Digital Active, Credit Heavy, Dormant Risk, Payroll Customer, SME Owner"),
    ("segment_score",                 "DOUBLE",  "Segment model confidence score (0-1)"),
    ("dormant_flag",                  "BOOLEAN", "True if customer is classified dormant"),
    ("dormant_risk_level",            "STRING",  "Dormant risk: HIGH / MEDIUM / LOW"),
    ("dormant_probability",           "DOUBLE",  "Dormant probability score (0-1)"),
    ("dormant_reason_code",           "STRING",  "Reason code: LOW_ACTIVITY, NO_DIGITAL_LOGIN, BALANCE_DECLINE, MATURED_DEPOSIT, LOW_TRANSACTION_COUNT, NORMAL_ACTIVITY"),
    ("recommended_campaign",          "STRING",  "Recommended campaign for customer"),
    ("recommended_channel",           "STRING",  "Recommended contact channel"),
    ("next_best_action",              "STRING",  "Recommended next action text"),
    ("credit_score",                  "INT",     "Credit score 300-850; higher is better"),
    ("credit_risk_label",             "STRING",  "Credit risk: GOOD (750+), FAIR (650-749), POOR (550-649), BAD (<550)"),
    ("churn_probability",             "DOUBLE",  "Churn probability score (0-1); higher = more likely to churn"),
    ("churn_risk_label",              "STRING",  "Churn risk level: HIGH (>=0.65), MEDIUM (0.35-0.64), LOW (<0.35)"),
    ("loan_type",                     "STRING",  "Loan type: KPR (mortgage), KKB (vehicle), KTA (unsecured), None"),
    ("digital_banking_adoption",      "STRING",  "Digital banking adoption: Active, Passive, None"),
    ("lat",                           "DOUBLE",  "Latitude coordinate (Indonesia-wide)"),
    ("lng",                           "DOUBLE",  "Longitude coordinate (Indonesia-wide)"),
]


def run_get_schema() -> dict:
    lines = [
        f"Tabel 1 (Agregasi & Segmentasi): {qualified_table()}",
        f"Nama pendek: {table_name()}",
        "",
        "PENTING — tabel ini sudah bertipe native:",
        "- status_rekening: 0=Aktif, 1=Dormant, 2=Tutup (integer langsung, tidak perlu CAST)",
        "- Cluster: 0=Silent Mature, 1=Young Syariah Digital, 2=Konvensional Produktif",
        "- RFM segment: Champions / Loyal / Potential / At Risk / Lost",
        "",
        f"Kolom Tabel 1 ({table_name()}):",
    ]
    for col, dtype, desc in COLUMNS:
        lines.append(f"  {col} ({dtype}) — {desc}")

    lines += [
        "",
        "Tabel 2 (Customer Dormant Segment — credit risk & churn): cai_sdx_se_indonesia.customer_dormant_segment",
        "",
        "PENTING — Tabel 2 field kunci:",
        "- credit_score: INT 300-850 (lebih tinggi = lebih baik)",
        "- credit_risk_label: GOOD/FAIR/POOR/BAD",
        "- churn_probability: FLOAT 0-1 (lebih tinggi = lebih berisiko churn)",
        "- churn_risk_label: HIGH/MEDIUM/LOW",
        "- dormant_risk_level: HIGH/MEDIUM/LOW",
        "- digital_banking_adoption: Active/Passive/None",
        "- loan_type: KPR/KKB/KTA/None",
        "- lat/lng: koordinat kota nasabah (seluruh Indonesia)",
        "",
        f"Kolom Tabel 2 (customer_dormant_segment):",
    ]
    for col, dtype, desc in CUSTOMER_DORMANT_SEGMENT_COLUMNS:
        lines.append(f"  {col} ({dtype}) — {desc}")

    return {
        "table": qualified_table(),
        "short_name": table_name(),
        "column_count": len(COLUMNS),
        "column_count_dormant_segment": len(CUSTOMER_DORMANT_SEGMENT_COLUMNS),
        "schema_info": "\n".join(lines),
    }
