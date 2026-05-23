-- =============================================================================
-- DDL: customer_segments
-- Source: customer_segments.parquet (219,262 rows, 37 columns)
-- Database: cai_sdx_se_indonesia
-- Upload parquet ke S3, Impala baca langsung — tidak perlu CSV
-- =============================================================================

-- STEP 1: Upload file parquet ke S3
-- Path: s3a://go01-demo/user/cai-demo-se-indonesia/data/customer_segments/
-- File: customer_segments.parquet

-- STEP 2: External table — baca langsung dari parquet di S3
-- Semua tipe kolom sesuai parquet, tidak perlu CAST STRING

CREATE EXTERNAL TABLE IF NOT EXISTS cai_sdx_se_indonesia.customer_segments_staging (
    cif                 STRING,
    no_rekening         STRING,
    jenis               STRING,
    jenis_rekening      STRING,
    cabang              STRING,
    saldo_t0            DOUBLE,
    total_tx            BIGINT,
    status_rekening     TINYINT,
    status_label        STRING,
    t0                  TIMESTAMP,
    umur                INT,
    jenis_kelamin       STRING,
    hari_sejak_trx      BIGINT,
    rasio_kredit        DOUBLE,
    cluster_kmeans      BIGINT,
    cluster_gmm         BIGINT,
    gmm_max_prob        DOUBLE,
    gmm_entropy         DOUBLE,
    gmm_p0              DOUBLE,
    gmm_p1              DOUBLE,
    gmm_p2              DOUBLE,
    gmm_p3              DOUBLE,
    gmm_p4              DOUBLE,
    gmm_p5              DOUBLE,
    gmm_p6              DOUBLE,
    gmm_p7              DOUBLE,
    cluster_label       STRING,
    cluster_color       STRING,
    age_group           STRING,
    jenis_kelamin_label STRING,
    saldo_segment       STRING,
    activity_level      STRING,
    rfm_r               BIGINT,
    rfm_f               BIGINT,
    rfm_m               BIGINT,
    rfm_score           BIGINT,
    rfm_segment         STRING
)
STORED AS PARQUET
LOCATION 's3a://go01-demo/user/cai-demo-se-indonesia/data/customer_segments/';


-- STEP 3: Verify staging
SELECT COUNT(*) AS total_rows FROM cai_sdx_se_indonesia.customer_segments_staging;
-- Expected: 219,262

SELECT * FROM cai_sdx_se_indonesia.customer_segments_staging LIMIT 5;


-- STEP 4 (opsional): Managed table untuk query lebih cepat
-- Jalankan hanya jika staging sudah verified

CREATE TABLE IF NOT EXISTS cai_sdx_se_indonesia.customer_segments
STORED AS PARQUET
AS
SELECT * FROM cai_sdx_se_indonesia.customer_segments_staging;

-- STEP 5: Verify managed table
SELECT COUNT(*) FROM cai_sdx_se_indonesia.customer_segments;
