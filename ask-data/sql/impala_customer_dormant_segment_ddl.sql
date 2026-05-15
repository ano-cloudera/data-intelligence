-- ============================================================
-- Bank Jawa Timur — customer_dormant_segment
-- Impala Native Table DDL (STORED AS PARQUET)
-- ============================================================
-- Usage:
--   1. Run STEP 0: create database (skip if exists)
--   2. Run STEP 1: create external staging table over CSV
--   3. Run STEP 2: create managed Parquet table
--   4. Run STEP 3: INSERT from staging into Parquet table
--   5. Run STEP 4: drop staging table
--   6. Run sanity checks
-- ============================================================


-- ─── STEP 0: Database ────────────────────────────────────────

CREATE DATABASE IF NOT EXISTS cai_sdx_se_indonesia;


-- ─── STEP 1: External staging table over CSV ─────────────────

CREATE EXTERNAL TABLE IF NOT EXISTS cai_sdx_se_indonesia.customer_dormant_segment_staging (
  customer_id                    STRING,
  snapshot_date                  STRING,
  age_band                       STRING,
  gender                         STRING,
  city                           STRING,
  district                       STRING,
  branch_code                    STRING,
  branch_name                    STRING,
  customer_tenure_months         INT,
  occupation_category            STRING,
  income_band                    STRING,
  customer_type                  STRING,
  total_accounts                 INT,
  has_savings                    STRING,
  has_current_account            STRING,
  has_deposit                    STRING,
  has_loan                       STRING,
  has_mobile_banking             STRING,
  has_internet_banking           STRING,
  product_holding_count          INT,
  avg_savings_balance_3m         DOUBLE,
  avg_deposit_balance_3m         DOUBLE,
  total_deposit_balance          DOUBLE,
  outstanding_loan_balance       DOUBLE,
  monthly_avg_transaction_amount DOUBLE,
  monthly_transaction_count      INT,
  days_since_last_transaction    INT,
  active_months_last_6m          INT,
  debit_transaction_count_3m     INT,
  credit_transaction_count_3m    INT,
  digital_login_count_3m         INT,
  atm_transaction_count_3m       INT,
  branch_transaction_count_3m    INT,
  customer_segment               STRING,
  segment_description            STRING,
  segment_score                  DOUBLE,
  dormant_flag                   STRING,
  dormant_risk_level             STRING,
  dormant_probability            DOUBLE,
  dormant_reason_code            STRING,
  recommended_campaign           STRING,
  recommended_channel            STRING,
  next_best_action               STRING,
  segmentation_model_version     STRING,
  dormant_model_version          STRING,
  scoring_timestamp              STRING
)
ROW FORMAT DELIMITED
  FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 's3a://go01-demo/user/cai-demo-se-indonesia/data/customer dormant segmentation/'
TBLPROPERTIES ('skip.header.line.count'='1');


-- ─── STEP 2: Managed Parquet table (target) ──────────────────

CREATE TABLE IF NOT EXISTS cai_sdx_se_indonesia.customer_dormant_segment (
  customer_id                    STRING,
  snapshot_date                  STRING,

  age_band                       STRING,
  gender                         STRING,
  city                           STRING,
  district                       STRING,
  branch_code                    STRING,
  branch_name                    STRING,
  customer_tenure_months         INT,
  occupation_category            STRING,
  income_band                    STRING,
  customer_type                  STRING,

  total_accounts                 INT,
  has_savings                    BOOLEAN,
  has_current_account            BOOLEAN,
  has_deposit                    BOOLEAN,
  has_loan                       BOOLEAN,
  has_mobile_banking             BOOLEAN,
  has_internet_banking           BOOLEAN,
  product_holding_count          INT,

  avg_savings_balance_3m         DOUBLE,
  avg_deposit_balance_3m         DOUBLE,
  total_deposit_balance          DOUBLE,
  outstanding_loan_balance       DOUBLE,
  monthly_avg_transaction_amount DOUBLE,
  monthly_transaction_count      INT,

  days_since_last_transaction    INT,
  active_months_last_6m          INT,
  debit_transaction_count_3m     INT,
  credit_transaction_count_3m    INT,
  digital_login_count_3m         INT,
  atm_transaction_count_3m       INT,
  branch_transaction_count_3m    INT,

  customer_segment               STRING,
  segment_description            STRING,
  segment_score                  DOUBLE,

  dormant_flag                   BOOLEAN,
  dormant_risk_level             STRING,
  dormant_probability            DOUBLE,
  dormant_reason_code            STRING,

  recommended_campaign           STRING,
  recommended_channel            STRING,
  next_best_action               STRING,

  segmentation_model_version     STRING,
  dormant_model_version          STRING,
  scoring_timestamp              STRING
)
STORED AS PARQUET;


-- ─── STEP 3: Load from staging into Parquet table ────────────

INSERT INTO cai_sdx_se_indonesia.customer_dormant_segment
SELECT
  customer_id,
  snapshot_date,
  age_band,
  gender,
  city,
  district,
  branch_code,
  branch_name,
  customer_tenure_months,
  occupation_category,
  income_band,
  customer_type,
  total_accounts,
  CASE WHEN lower(has_savings)          = 'true' THEN true ELSE false END,
  CASE WHEN lower(has_current_account)  = 'true' THEN true ELSE false END,
  CASE WHEN lower(has_deposit)          = 'true' THEN true ELSE false END,
  CASE WHEN lower(has_loan)             = 'true' THEN true ELSE false END,
  CASE WHEN lower(has_mobile_banking)   = 'true' THEN true ELSE false END,
  CASE WHEN lower(has_internet_banking) = 'true' THEN true ELSE false END,
  product_holding_count,
  avg_savings_balance_3m,
  avg_deposit_balance_3m,
  total_deposit_balance,
  outstanding_loan_balance,
  monthly_avg_transaction_amount,
  monthly_transaction_count,
  days_since_last_transaction,
  active_months_last_6m,
  debit_transaction_count_3m,
  credit_transaction_count_3m,
  digital_login_count_3m,
  atm_transaction_count_3m,
  branch_transaction_count_3m,
  customer_segment,
  segment_description,
  segment_score,
  CASE WHEN lower(dormant_flag) = 'true' THEN true ELSE false END,
  dormant_risk_level,
  dormant_probability,
  dormant_reason_code,
  recommended_campaign,
  recommended_channel,
  next_best_action,
  segmentation_model_version,
  dormant_model_version,
  scoring_timestamp
FROM cai_sdx_se_indonesia.customer_dormant_segment_staging;


-- ─── STEP 4: Drop staging table ──────────────────────────────

DROP TABLE IF EXISTS cai_sdx_se_indonesia.customer_dormant_segment_staging;


-- ─── Sanity checks ───────────────────────────────────────────

SELECT COUNT(*) FROM cai_sdx_se_indonesia.customer_dormant_segment;

SELECT customer_segment, COUNT(*) AS jumlah_nasabah
FROM cai_sdx_se_indonesia.customer_dormant_segment
GROUP BY customer_segment
ORDER BY jumlah_nasabah DESC;

SELECT dormant_risk_level,
       COUNT(*)                          AS jumlah,
       ROUND(AVG(dormant_probability),4) AS avg_prob
FROM cai_sdx_se_indonesia.customer_dormant_segment
GROUP BY dormant_risk_level
ORDER BY avg_prob DESC;

SELECT city, COUNT(*) AS jumlah_nasabah
FROM cai_sdx_se_indonesia.customer_dormant_segment
GROUP BY city
ORDER BY jumlah_nasabah DESC
LIMIT 10;
