# Metadata: `cai_sdx_se_indonesia.customer_dormant_segment`

> **Purpose of this document**
> Complete schema dictionary and business glossary for the Bank Jawa Timur AI analytics assistant.
> This file is the single source of truth for LLM context injection, human review, and onboarding.

---

## 1. Table Overview

| Attribute        | Value                                              |
|------------------|----------------------------------------------------|
| **Database**     | `cai_sdx_se_indonesia`                                        |
| **Table**        | `customer_dormant_segment`                              |
| **Format**       | Apache Iceberg (Parquet, Snappy)                   |
| **Grain**        | One row per `customer_id` per `snapshot_date`      |
| **Primary use**  | Customer segmentation, dormant risk analysis, campaign recommendation, branch & channel analytics |
| **Data origin**  | Synthetic — no real PII. `customer_id` is an analytics-only identifier. |
| **Snapshot cadence** | Monthly (last snapshot: beginning of each month) |

---

## 2. Schema Dictionary

### 2.1 Identity & Snapshot

| Column | Type | Description | Example values |
|--------|------|-------------|----------------|
| `customer_id` | STRING | Synthetic analytics identifier. **Not a real CIF or account number.** | `CUST000000001` |
| `snapshot_date` | STRING | Date of the AI scoring snapshot. Format: `YYYY-MM-DD`. Use `substr(snapshot_date,1,7)` for monthly grouping. | `2026-05-01` |

### 2.2 Demographics

| Column | Type | Description | Example values |
|--------|------|-------------|----------------|
| `age_band` | STRING | Customer age group | `18-25`, `26-35`, `36-45`, `46-55`, `56-65`, `>65` |
| `gender` | STRING | Customer gender | `M`, `F` |
| `city` | STRING | Customer's registered city | `Surabaya`, `Malang`, `Sidoarjo`, `Kediri`, `Madiun`, `Jember`, `Banyuwangi`, `Gresik`, `Pasuruan`, `Bojonegoro` |
| `district` | STRING | Customer's district (same granularity as city in this dataset) | `Surabaya` |
| `branch_code` | STRING | Home branch code | `BJTM101`, `BJTM245` |
| `branch_name` | STRING | Home branch name | `Cabang Basuki Rahmat`, `Cabang Malang Kawi` |
| `customer_tenure_months` | INT | Months since customer onboarding | `3` – `240` |
| `occupation_category` | STRING | Customer's occupation category | `Pegawai`, `Wiraswasta`, `Pensiunan`, `Profesional`, `Pelajar`, `Petani/Nelayan`, `UMKM` |
| `income_band` | STRING | Monthly income band | `<5jt`, `5-10jt`, `10-25jt`, `25-50jt`, `>50jt` |
| `customer_type` | STRING | Customer classification | `Individual`, `SME` |

### 2.3 Product Holding

| Column | Type | Description | Typical values |
|--------|------|-------------|----------------|
| `total_accounts` | INT | Total number of accounts | `1` – `6` |
| `has_savings` | BOOLEAN | Customer has at least one savings account | `true`, `false` |
| `has_current_account` | BOOLEAN | Customer has a current/giro account | `true`, `false` |
| `has_deposit` | BOOLEAN | Customer has at least one time deposit (deposito berjangka) | `true`, `false` |
| `has_loan` | BOOLEAN | Customer has an active loan | `true`, `false` |
| `has_mobile_banking` | BOOLEAN | Customer is enrolled in mobile banking | `true`, `false` |
| `has_internet_banking` | BOOLEAN | Customer is enrolled in internet banking | `true`, `false` |
| `product_holding_count` | INT | Total number of distinct products held | `1` – `5` |

### 2.4 Balance & Transaction Metrics

| Column | Type | Unit | Description |
|--------|------|------|-------------|
| `avg_savings_balance_3m` | DECIMAL(18,2) | IDR | Average savings account balance over the last 3 months |
| `avg_deposit_balance_3m` | DECIMAL(18,2) | IDR | Average time deposit balance over the last 3 months |
| `total_deposit_balance` | DECIMAL(18,2) | IDR | Total current time deposit balance |
| `outstanding_loan_balance` | DECIMAL(18,2) | IDR | Total outstanding loan principal balance |
| `monthly_avg_transaction_amount` | DECIMAL(18,2) | IDR | Average total transaction amount per month |
| `monthly_transaction_count` | INT | Count | Average number of transactions per month |

### 2.5 Behavioral Features

| Column | Type | Description |
|--------|------|-------------|
| `days_since_last_transaction` | INT | Days elapsed since the customer's last recorded transaction. High value = lower activity. |
| `active_months_last_6m` | INT | Number of months (out of 6) where the customer had at least one transaction. Range: `0`–`6`. |
| `debit_transaction_count_3m` | INT | Total debit (outgoing) transaction count in last 3 months |
| `credit_transaction_count_3m` | INT | Total credit (incoming) transaction count in last 3 months |
| `digital_login_count_3m` | INT | Number of logins via mobile banking or internet banking in last 3 months |
| `atm_transaction_count_3m` | INT | ATM transaction count in last 3 months |
| `branch_transaction_count_3m` | INT | In-branch (teller) transaction count in last 3 months |

### 2.6 Segmentation Model Output

| Column | Type | Description |
|--------|------|-------------|
| `customer_segment` | STRING | Segment label assigned by the KMeans segmentation model. See §4 for full list. |
| `segment_description` | STRING | Human-readable description of the segment (in Bahasa Indonesia) |
| `segment_score` | DOUBLE | Segmentation model confidence score. Range: `0.0`–`1.0`. Higher = stronger segment fit. |

### 2.7 Dormant Risk Model Output

| Column | Type | Description |
|--------|------|-------------|
| `dormant_flag` | BOOLEAN | `true` if the customer is classified as dormant (dormant_probability ≥ 0.70) |
| `dormant_risk_level` | STRING | Tiered risk label. `HIGH` (≥0.70), `MEDIUM` (0.40–0.69), `LOW` (<0.40) |
| `dormant_probability` | DOUBLE | Dormancy probability score from the XGBoost model. Range: `0.0`–`1.0`. |
| `dormant_reason_code` | STRING | Primary reason code for the dormancy classification. See §5 for full list. |

### 2.8 Campaign & Action Recommendation

| Column | Type | Description |
|--------|------|-------------|
| `recommended_campaign` | STRING | Campaign name recommended for this customer. See §6 for full list. |
| `recommended_channel` | STRING | Preferred contact channel for the recommended campaign. See §7 for full list. |
| `next_best_action` | STRING | Free-text description of the recommended next action for the RM or system. |

### 2.9 Model Metadata

| Column | Type | Description |
|--------|------|-------------|
| `segmentation_model_version` | STRING | Version tag of the segmentation model used for this row | `segmentation-kmeans-v1` |
| `dormant_model_version` | STRING | Version tag of the dormant risk model used for this row | `dormant-xgboost-v1` |
| `scoring_timestamp` | STRING | Datetime when the scoring pipeline last ran. Format: `YYYY-MM-DD HH:MM:SS` |

---

## 3. Business Glossary

This section maps business terms (as used by Bank Jatim analysts) to their SQL equivalents.

| Business term (Bahasa Indonesia) | English equivalent | SQL filter / column |
|-----------------------------------|--------------------|---------------------|
| Nasabah dormant | Dormant customer | `dormant_flag = true` |
| Risiko dormant tinggi | High dormant risk | `dormant_risk_level = 'HIGH'` |
| Risiko dormant menengah | Medium dormant risk | `dormant_risk_level = 'MEDIUM'` |
| Risiko dormant rendah | Low dormant risk | `dormant_risk_level = 'LOW'` |
| Probabilitas dormant | Dormancy probability | `dormant_probability` |
| Segmentasi nasabah | Customer segmentation | `customer_segment` |
| Segmen nasabah | Customer segment | `customer_segment` |
| Saldo deposito | Deposit balance | `total_deposit_balance` |
| Saldo tabungan | Savings balance | `avg_savings_balance_3m` |
| Saldo pinjaman / kredit | Loan balance | `outstanding_loan_balance` |
| Nasabah penabung aktif | Active savings customer | `has_savings = true AND days_since_last_transaction <= 30` |
| Nasabah digital | Digital banking customer | `has_mobile_banking = true OR has_internet_banking = true` |
| Nasabah tidak aktif digital | Digitally inactive customer | `has_mobile_banking = false AND has_internet_banking = false` |
| Nasabah kredit / pinjaman | Loan customer | `has_loan = true` |
| Nasabah deposito | Time deposit customer | `has_deposit = true` |
| Nasabah lama / senior | Tenured customer | `customer_tenure_months >= 60` |
| Nasabah baru | New customer | `customer_tenure_months <= 12` |
| Frekuensi transaksi | Transaction frequency | `monthly_transaction_count` |
| Aktivitas digital | Digital activity | `digital_login_count_3m` |
| Rekomendasi campaign | Campaign recommendation | `recommended_campaign` |
| Channel rekomendasi | Recommended channel | `recommended_channel` |
| Tindakan terbaik | Next best action | `next_best_action` |
| Cabang / kantor cabang | Branch | `branch_name` |
| Kota | City | `city` |
| Segmen SME | SME customers | `customer_type = 'SME'` |
| Nasabah perorangan | Individual customers | `customer_type = 'Individual'` |
| Per bulan | Monthly / by month | `substr(snapshot_date, 1, 7)` |
| Bulan ini | Current month | `substr(snapshot_date, 1, 7) = '2026-05'` |

---

## 4. Customer Segment Reference

| Segment label | Bahasa description | Key characteristics |
|---------------|--------------------|---------------------|
| `Affluent Depositor` | Nasabah saldo tinggi dengan kepemilikan deposito kuat | High `total_deposit_balance`, high `avg_savings_balance_3m`, low dormant probability |
| `Mass Retail` | Nasabah retail umum dengan transaksi reguler | Moderate balances, regular transaction frequency, mixed product holding |
| `Digital Active` | Nasabah aktif di channel digital | High `digital_login_count_3m`, frequent mobile/internet banking, high `monthly_transaction_count` |
| `Credit Heavy` | Nasabah dengan eksposur pinjaman tinggi | High `outstanding_loan_balance`, `has_loan = true` |
| `Dormant Risk` | Nasabah dengan aktivitas rendah dan risiko dormant | High `days_since_last_transaction`, low `active_months_last_6m`, high `dormant_probability` |
| `Payroll Customer` | Nasabah payroll aktif | Regular credit inflows (`credit_transaction_count_3m`), consistent activity |
| `SME Owner` | Nasabah pemilik usaha kecil dan menengah | `customer_type = 'SME'`, mixed loan + savings, higher balance volatility |

---

## 5. Dormant Reason Code Reference

| Reason code | Meaning |
|-------------|---------|
| `LOW_ACTIVITY` | Overall low transaction frequency across all channels |
| `NO_DIGITAL_LOGIN` | No digital banking logins in the last 3 months |
| `BALANCE_DECLINE` | Significant decline in savings or deposit balance |
| `MATURED_DEPOSIT` | Time deposit matured and not renewed |
| `LOW_TRANSACTION_COUNT` | Transaction count fell below threshold |
| `NORMAL_ACTIVITY` | No dormant signal detected — normal behavioral pattern |

---

## 6. Campaign Reference

| Campaign name | Target condition |
|---------------|-----------------|
| `Reaktivasi Dormant` | `dormant_risk_level = 'HIGH'` — priority reactivation outreach |
| `Cross-sell Deposito` | Affluent segment with high savings but no active deposit |
| `Upgrade Digital Banking` | Customers with `has_mobile_banking = false` or low `digital_login_count_3m` |
| `Loan Restructure Outreach` | High `outstanding_loan_balance`, `has_loan = true` |
| `Payroll Bundle` | Payroll customers eligible for bundled product offers |
| `SME Advisory` | `customer_type = 'SME'` — business banking advisory engagement |

---

## 7. Recommended Channel Reference

| Channel | Typical use case |
|---------|-----------------|
| `Mobile Banking` | Digital-first customers, self-service campaigns |
| `Relationship Manager` | Affluent and SME segments requiring personal advisory |
| `Branch Outreach` | High-value dormant reactivation, in-person engagement |
| `SMS Campaign` | Broad outreach for mass retail and dormant segments |
| `Call Center` | High-risk dormant, loan restructuring, follow-up after SMS |

---

## 8. Query Writing Rules for AI

These rules **must always** be applied when generating SQL against this table.

1. **Only query `cai_sdx_se_indonesia.customer_dormant_segment`.** No joins to any other table.
2. **Never use `SELECT *`.** Always select only the columns needed to answer the question.
3. **Aggregate by default.** For business questions, prefer `COUNT`, `AVG`, `SUM`, `GROUP BY`.
4. **Always LIMIT row-level queries.** Any query returning individual rows must have `LIMIT 20`.
5. **Date grouping:** Use `substr(snapshot_date, 1, 7)` for monthly grouping. **Do not use `date_format()`** — it is not supported in this Impala version.
6. **Currency formatting:** All balance columns are in IDR (Indonesian Rupiah). Present values in millions (juta) or billions (miliar) for readability.
7. **Dormant interpretation:** `dormant_flag = true` means `dormant_probability >= 0.70`. Do not combine `dormant_flag` with manual probability thresholds — pick one approach.
8. **Segment filtering:** `customer_segment` values are exact strings. Always quote them exactly as shown in §4.
9. **Boolean columns:** In Impala, filter with `= true` or `= false`. Do not use `IS TRUE` or `!= 0`.
10. **PII guardrail:** Never surface `customer_id` as a meaningful business field. It may only appear as an anonymous count or as a filter anchor — never in a way that correlates it to any personal attribute.

---

## 9. Sample Business Questions & SQL

### Q1: Berapa nasabah per segmen?

```sql
SELECT customer_segment,
       COUNT(*) AS jumlah_nasabah
FROM cai_sdx_se_indonesia.customer_dormant_segment
GROUP BY customer_segment
ORDER BY jumlah_nasabah DESC;
```

### Q2: Distribusi nasabah dormant berdasarkan kota

```sql
SELECT city,
       SUM(CASE WHEN dormant_flag = true THEN 1 ELSE 0 END) AS dormant_count,
       COUNT(*) AS total_nasabah,
       ROUND(
         SUM(CASE WHEN dormant_flag = true THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2
       ) AS dormant_pct
FROM cai_sdx_se_indonesia.customer_dormant_segment
GROUP BY city
ORDER BY dormant_count DESC;
```

### Q3: Rata-rata saldo deposito nasabah dormant HIGH vs LOW

```sql
SELECT dormant_risk_level,
       COUNT(*)                                AS jumlah,
       ROUND(AVG(total_deposit_balance), 2)   AS avg_saldo_deposito,
       ROUND(AVG(dormant_probability), 4)     AS avg_prob_dormant
FROM cai_sdx_se_indonesia.customer_dormant_segment
GROUP BY dormant_risk_level
ORDER BY avg_prob_dormant DESC;
```

### Q4: Top 10 cabang berdasarkan jumlah nasabah risiko dormant tinggi

```sql
SELECT branch_name,
       COUNT(*) AS nasabah_dormant_high
FROM cai_sdx_se_indonesia.customer_dormant_segment
WHERE dormant_risk_level = 'HIGH'
GROUP BY branch_name
ORDER BY nasabah_dormant_high DESC
LIMIT 10;
```

### Q5: Nasabah digital aktif yang belum punya deposito

```sql
SELECT customer_segment,
       COUNT(*) AS jumlah
FROM cai_sdx_se_indonesia.customer_dormant_segment
WHERE has_mobile_banking = true
  AND has_deposit = false
GROUP BY customer_segment
ORDER BY jumlah DESC;
```

### Q6: Tren nasabah dormant per bulan snapshot

```sql
SELECT substr(snapshot_date, 1, 7)           AS bulan,
       SUM(CASE WHEN dormant_flag = true THEN 1 ELSE 0 END) AS dormant_count,
       COUNT(*)                               AS total
FROM cai_sdx_se_indonesia.customer_dormant_segment
GROUP BY substr(snapshot_date, 1, 7)
ORDER BY bulan;
```

---

## 10. Model Information

| Model | Version | Algorithm | Output columns |
|-------|---------|-----------|----------------|
| Segmentation | `segmentation-kmeans-v1` | KMeans clustering | `customer_segment`, `segment_description`, `segment_score` |
| Dormant Risk | `dormant-xgboost-v1` | XGBoost binary classifier | `dormant_flag`, `dormant_risk_level`, `dormant_probability`, `dormant_reason_code` |

**Scoring pipeline:** Both models run monthly. Each snapshot produces a new set of rows with the current `snapshot_date`. Historical snapshots are retained in the same table (Iceberg enables time-travel queries if needed).
