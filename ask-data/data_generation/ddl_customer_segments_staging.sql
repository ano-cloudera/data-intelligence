-- =============================================================================
-- DDL: customer_segments_staging — Bank XYZ Demo
-- Updated: tambah credit_score, credit_risk_label, churn_probability,
--          churn_risk_label, loan_type, digital_banking_adoption
-- =============================================================================

DROP TABLE IF EXISTS cai_sdx_se_indonesia.customer_segments_staging;

CREATE EXTERNAL TABLE cai_sdx_se_indonesia.customer_segments_staging (
    cif                      STRING,
    no_rekening              STRING,
    jenis                    STRING,
    jenis_rekening           STRING,
    cabang                   STRING,
    saldo_t0                 DOUBLE,
    total_tx                 BIGINT,
    status_rekening          TINYINT,
    status_label             STRING,
    t0                       TIMESTAMP,
    umur                     INT,
    jenis_kelamin            STRING,
    hari_sejak_trx           BIGINT,
    rasio_kredit             DOUBLE,
    cluster_kmeans           BIGINT,
    cluster_gmm              BIGINT,
    gmm_max_prob             DOUBLE,
    gmm_entropy              DOUBLE,
    gmm_p0                   DOUBLE,
    gmm_p1                   DOUBLE,
    gmm_p2                   DOUBLE,
    gmm_p3                   DOUBLE,
    gmm_p4                   DOUBLE,
    gmm_p5                   DOUBLE,
    gmm_p6                   DOUBLE,
    gmm_p7                   DOUBLE,
    cluster_label            STRING,
    cluster_color            STRING,
    age_group                STRING,
    jenis_kelamin_label      STRING,
    saldo_segment            STRING,
    activity_level           STRING,
    rfm_r                    BIGINT,
    rfm_f                    BIGINT,
    rfm_m                    BIGINT,
    rfm_score                BIGINT,
    rfm_segment              STRING,
    cabang_name              STRING,
    kota                     STRING,
    lat                      DOUBLE,
    lng                      DOUBLE,
    -- NEW: Credit Risk & Churn columns
    credit_score             BIGINT,
    credit_risk_label        STRING,
    churn_probability        DOUBLE,
    churn_risk_label         STRING,
    loan_type                STRING,
    digital_banking_adoption STRING
)
STORED AS PARQUET
LOCATION 's3a://go01-demo/user/cai-demo-se-indonesia/data/customer segmentation parquet/';

-- Verify table created
SELECT * FROM cai_sdx_se_indonesia.customer_segments_staging LIMIT 5;

-- Sanity check: cabang distribution
SELECT cabang, cabang_name, kota, lat, lng, COUNT(*) AS total
FROM cai_sdx_se_indonesia.customer_segments_staging
GROUP BY cabang, cabang_name, kota, lat, lng
ORDER BY total DESC
LIMIT 10;

-- Quick check new columns
SELECT
    credit_risk_label,
    churn_risk_label,
    loan_type,
    digital_banking_adoption,
    COUNT(*)              AS jumlah,
    AVG(credit_score)     AS avg_credit_score,
    AVG(churn_probability) AS avg_churn_prob
FROM cai_sdx_se_indonesia.customer_segments_staging
GROUP BY credit_risk_label, churn_risk_label, loan_type, digital_banking_adoption
ORDER BY jumlah DESC
LIMIT 20;
