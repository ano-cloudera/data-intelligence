-- =============================================================
-- customer_360_agent_studio — Impala External Table DDL
-- Jasa Raharja Agent Demo — Customer 360 Synthetic Dataset
-- Generated: 2026-07-10
--
-- External table langsung pointing ke CSV di S3.
-- Tidak perlu staging + INSERT — query langsung dari file.
-- =============================================================

DROP TABLE IF EXISTS cai_sdx_se_indonesia.customer_360_agent_studio;

CREATE EXTERNAL TABLE cai_sdx_se_indonesia.customer_360_agent_studio (
    customer_id         STRING          COMMENT 'Unique synthetic customer identifier. Example: CUST000001',
    customer_type       STRING          COMMENT 'Individual or Organization',
    customer_name       STRING          COMMENT 'Customer display name',
    gender              STRING          COMMENT 'Male / Female / N/A for organizations',
    birth_date          STRING          COMMENT 'Date of birth (empty for organizations)',
    age                 INT             COMMENT 'Age in completed years (NULL for organizations)',
    city                STRING          COMMENT 'City of customer or vehicle registration',
    province            STRING          COMMENT 'Province of customer or vehicle registration',
    latitude            DOUBLE          COMMENT 'Approximate latitude for mapping',
    longitude           DOUBLE          COMMENT 'Approximate longitude for mapping',
    vehicle_id          STRING          COMMENT 'Unique synthetic vehicle identifier. Example: VEH000001',
    vehicle_type        STRING          COMMENT 'Motorcycle / Passenger Car / Truck / Bus / Commercial Vehicle',
    vehicle_brand       STRING          COMMENT 'Vehicle manufacturer. Examples: Toyota, Honda, Suzuki',
    vehicle_year        INT             COMMENT 'Vehicle manufacturing year',
    vehicle_age         INT             COMMENT 'Vehicle age in years',
    plate_region        STRING          COMMENT 'Regional prefix of vehicle registration plate. Example: B, D, L',
    organization_name   STRING          COMMENT 'Organization name (NULL for individuals)',
    transaction_id      STRING          COMMENT 'Unique synthetic transaction identifier. Example: TRX000001',
    transaction_date    STRING          COMMENT 'Date of latest Sumbangan Wajib transaction',
    last_payment_date   STRING          COMMENT 'Most recent payment date',
    payment_status      STRING          COMMENT 'Paid / Overdue / Due Soon / Installment',
    sw_amount           BIGINT          COMMENT 'Sumbangan Wajib amount in IDR',
    penalty_amount      BIGINT          COMMENT 'Late fee amount in IDR (0 if none)',
    claim_id            STRING          COMMENT 'Claim identifier (empty if no claim)',
    claim_count         INT             COMMENT 'Number of claims (0 if none)',
    claim_amount        BIGINT          COMMENT 'Total claim amount in IDR',
    journal_amount      BIGINT          COMMENT 'Total journal amount (sw_amount + penalty_amount)',
    inflation_rate      DOUBLE          COMMENT 'Inflation rate as percentage points',
    weather_condition   STRING          COMMENT 'Sunny / Cloudy / Rainy / Heavy Rain',
    economic_index      DOUBLE          COMMENT 'Synthetic macroeconomic index',
    segment             STRING          COMMENT 'Premium / Growth / Standard / At Risk',
    renewal_probability DOUBLE          COMMENT 'Predicted renewal probability. Range 0-1',
    cross_sell_score    DOUBLE          COMMENT 'Cross-sell suitability score. Range 0-1',
    retention_score     DOUBLE          COMMENT 'Retention likelihood score. Range 0-1',
    churn_risk          DOUBLE          COMMENT 'Churn risk score. Range 0-1. High risk >= 0.60',
    preferred_channel   STRING          COMMENT 'SMS / Call Center / WhatsApp / Mobile App / Email',
    last_campaign       STRING          COMMENT 'Most recent campaign name',
    campaign_response   STRING          COMMENT 'Not Contacted / No Response / Opened / Clicked / Converted',
    predicted_revenue   BIGINT          COMMENT 'Estimated future revenue in IDR',
    data_quality_score  DOUBLE          COMMENT 'Record completeness score. Range 0-1'
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
STORED AS TEXTFILE
LOCATION 's3a://go01-demo/user/cai-demo-se-indonesia/data/customer360'
TBLPROPERTIES ('skip.header.line.count'='1');


-- Refresh metadata
INVALIDATE METADATA cai_sdx_se_indonesia.customer_360_agent_studio;
COMPUTE STATS cai_sdx_se_indonesia.customer_360_agent_studio;


-- Validation
SELECT COUNT(*) AS row_count FROM cai_sdx_se_indonesia.customer_360_agent_studio;

SELECT
    segment,
    COUNT(*)                            AS customers,
    ROUND(AVG(renewal_probability), 4)  AS avg_renewal_prob,
    ROUND(AVG(cross_sell_score), 4)     AS avg_cross_sell,
    ROUND(AVG(churn_risk), 4)           AS avg_churn_risk
FROM cai_sdx_se_indonesia.customer_360_agent_studio
GROUP BY segment
ORDER BY customers DESC;
