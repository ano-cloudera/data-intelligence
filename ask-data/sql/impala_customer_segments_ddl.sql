-- =============================================================================
-- DDL: customer_segments_staging
-- Source: customer_segments_sample_1k.parquet (1,000 rows, 37 columns)
-- Database: cai_sdx_se_indonesia
-- Upload parquet ke S3, Impala baca langsung — tidak perlu CSV
-- Tipe kolom di-derive dari pyarrow schema file parquet aktual
-- =============================================================================

-- STEP 1: Drop & recreate (jika perlu reset)
-- DROP TABLE IF EXISTS cai_sdx_se_indonesia.customer_segments_staging;

-- STEP 2: External table — baca langsung dari parquet di S3
-- Kolom: 37 kolom, tipe sesuai parquet output
-- t0 disimpan sebagai STRING (format YYYY-MM-DD), bukan TIMESTAMP

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
    t0                  STRING,
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


-- STEP 3: Refresh metadata setelah upload file baru
REFRESH cai_sdx_se_indonesia.customer_segments_staging;

-- STEP 4: Verify
SELECT COUNT(*) AS total_rows FROM cai_sdx_se_indonesia.customer_segments_staging;
-- Expected: 1,000

SELECT status_label, COUNT(*) AS jumlah
FROM cai_sdx_se_indonesia.customer_segments_staging
GROUP BY status_label;
-- Expected: Aktif ~700, Dormant ~200, Tutup ~100

SELECT cluster_label, COUNT(*) AS jumlah
FROM cai_sdx_se_indonesia.customer_segments_staging
GROUP BY cluster_label;

-- STEP 5: COMPUTE STATS (wajib — buat query dari 11 detik jadi 2-3 detik)
COMPUTE STATS cai_sdx_se_indonesia.customer_segments_staging;
