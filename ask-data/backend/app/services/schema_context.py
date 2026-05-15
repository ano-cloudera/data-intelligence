from __future__ import annotations


def build_database_description() -> str:
    return (
        "Database purpose: Bank Jawa Timur customer analytics platform. "
        "Main use case: customer segmentation, dormant risk analysis, campaign recommendation, "
        "and branch/channel performance analytics."
    )


def build_table_descriptions() -> str:
    return """
Table: cai_sdx_se_indonesia.customer_dormant_segment
- Business meaning: AI-enriched customer profile for segmentation and dormant risk scoring
- Grain: one row per customer per snapshot date
- Columns:
  - customer_id: synthetic analytics identifier (not real PII)
  - snapshot_date: date of the scoring snapshot
  - age_band: customer age group (e.g. 26-35, 36-45)
  - gender: customer gender (M/F)
  - city: customer city
  - district: customer district
  - branch_code: branch code
  - branch_name: branch name
  - customer_tenure_months: months since customer onboarding
  - occupation_category: customer occupation category
  - income_band: customer income band
  - customer_type: Individual or SME
  - total_accounts: total number of accounts held
  - has_savings: boolean, customer has savings account
  - has_current_account: boolean, customer has current account
  - has_deposit: boolean, customer has deposit account
  - has_loan: boolean, customer has active loan
  - has_mobile_banking: boolean, customer enrolled in mobile banking
  - has_internet_banking: boolean, customer enrolled in internet banking
  - product_holding_count: total number of products held
  - avg_savings_balance_3m: average savings balance over last 3 months
  - avg_deposit_balance_3m: average deposit balance over last 3 months
  - total_deposit_balance: total current deposit balance
  - outstanding_loan_balance: total outstanding loan balance
  - monthly_avg_transaction_amount: average monthly transaction amount
  - monthly_transaction_count: average monthly transaction count
  - days_since_last_transaction: days since the last recorded transaction
  - active_months_last_6m: number of active months in the last 6 months
  - debit_transaction_count_3m: debit transaction count in last 3 months
  - credit_transaction_count_3m: credit transaction count in last 3 months
  - digital_login_count_3m: digital channel login count in last 3 months
  - atm_transaction_count_3m: ATM transaction count in last 3 months
  - branch_transaction_count_3m: branch transaction count in last 3 months
  - customer_segment: customer segment label (e.g. Affluent Depositor, Mass Retail, Digital Active)
  - segment_description: segment description text
  - segment_score: segment model confidence score (0-1)
  - dormant_flag: boolean, true if customer is classified as dormant
  - dormant_risk_level: dormant risk level: HIGH, MEDIUM, or LOW
  - dormant_probability: dormant probability score (0-1)
  - dormant_reason_code: reason code for dormant classification
  - recommended_campaign: recommended campaign for the customer
  - recommended_channel: recommended contact channel
  - next_best_action: recommended next action text
  - segmentation_model_version: version of the segmentation model used
  - dormant_model_version: version of the dormant risk model used
  - scoring_timestamp: timestamp when scoring was last run
""".strip()


def build_relationship_guidance() -> str:
    return """
Query guidance:
- Only query cai_sdx_se_indonesia.customer_dormant_segment.
- Do not join to any other table.
- For business questions, prefer aggregate queries (COUNT, SUM, AVG, GROUP BY).
- For row-level or top-N queries, always include LIMIT 20.
- Never use SELECT *.
- Never expose PII columns. customer_id is allowed only as an analytics identifier.
- Business term mapping:
  - "risiko dormant tinggi" => dormant_risk_level = 'HIGH'
  - "dormant high risk" => dormant_risk_level = 'HIGH'
  - "nasabah dormant" => dormant_flag = true
  - "segmentasi" => customer_segment
  - "customer segment" => customer_segment
  - "rekomendasi campaign" => recommended_campaign
  - "channel rekomendasi" => recommended_channel
  - "cabang" => branch_name
  - "kota" => city
  - "saldo deposito" => total_deposit_balance
  - "saldo pinjaman" => outstanding_loan_balance
  - "probability dormant" => dormant_probability
""".strip()


def build_schema_context() -> str:
    return "\n\n".join(
        (
            build_database_description(),
            build_table_descriptions(),
            build_relationship_guidance(),
        )
    )
