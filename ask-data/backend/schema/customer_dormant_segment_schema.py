"""
Schema registry for customer_dormant_segment.
Used to build LLM prompt context and validate allowed table/columns.
"""

ALLOWED_TABLE = "cai_sdx_se_indonesia.customer_dormant_segment"

COLUMNS = [
    "customer_id",
    "snapshot_date",
    "age_band",
    "gender",
    "city",
    "district",
    "branch_code",
    "branch_name",
    "customer_tenure_months",
    "occupation_category",
    "income_band",
    "customer_type",
    "total_accounts",
    "has_savings",
    "has_current_account",
    "has_deposit",
    "has_loan",
    "has_mobile_banking",
    "has_internet_banking",
    "product_holding_count",
    "avg_savings_balance_3m",
    "avg_deposit_balance_3m",
    "total_deposit_balance",
    "outstanding_loan_balance",
    "monthly_avg_transaction_amount",
    "monthly_transaction_count",
    "days_since_last_transaction",
    "active_months_last_6m",
    "debit_transaction_count_3m",
    "credit_transaction_count_3m",
    "digital_login_count_3m",
    "atm_transaction_count_3m",
    "branch_transaction_count_3m",
    "customer_segment",
    "segment_description",
    "segment_score",
    "dormant_flag",
    "dormant_risk_level",
    "dormant_probability",
    "dormant_reason_code",
    "recommended_campaign",
    "recommended_channel",
    "next_best_action",
    "segmentation_model_version",
    "dormant_model_version",
    "scoring_timestamp",
]

BLOCKED_PII_TERMS = [
    "nomor rekening",
    "rekening nasabah",
    "nik",
    "ktp",
    "cif",
    "nomor hp",
    "no hp",
    "handphone",
    "email",
    "alamat",
    "address",
    "phone",
    "mobile number",
]

STARTER_PROMPTS_ID = [
    "Tampilkan jumlah nasabah berdasarkan customer segment.",
    "Segmen mana yang memiliki risiko dormant paling tinggi?",
    "Berapa total saldo deposito untuk nasabah dormant risk high?",
    "Cabang mana yang memiliki rata-rata dormant probability tertinggi?",
    "Apa rekomendasi campaign untuk nasabah dormant high risk?",
]
