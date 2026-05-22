-- =============================================================
-- customer_aggregation — Impala DDL
-- Bank Jawa Timur PoC
-- Generated: 2026-05-22
--
-- Steps:
--   1. Create external staging table over CSV
--   2. Create managed Parquet table
--   3. INSERT with type casts
--   4. Drop staging table
--   5. Sanity check
-- =============================================================

-- STEP 1: External staging table (CSV)
-- Upload customer_aggregation_100.csv to HDFS/S3 first, then:

CREATE EXTERNAL TABLE IF NOT EXISTS cai_sdx_se_indonesia.customer_aggregation_staging (
    cif                 STRING,
    no_rekening         STRING,
    jenis               STRING,
    name                STRING,
    cabang              STRING,
    jenis_rekening      STRING,
    name_cabang         STRING,
    min_saldo           STRING,
    saldo_t0            STRING,
    tgl_trx_terakhir    STRING,
    total_tx            STRING,
    tx_sistem           STRING,
    tx_nasabah          STRING,
    count_tx_kredit     STRING,
    avg_nominal_kredit  STRING,
    max_nominal_kredit  STRING,
    min_nominal_kredit  STRING,
    std_nominal_kredit  STRING,
    count_tx_debit      STRING,
    avg_nominal_debit   STRING,
    max_nominal_debit   STRING,
    min_nominal_debit   STRING,
    std_nominal_debit   STRING,
    has_tx_first_6m     STRING,
    has_tx_last_6m      STRING,
    saldo_end_target    STRING,
    status_rekening     STRING,
    t0                  STRING
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
STORED AS TEXTFILE
LOCATION 's3a://<YOUR_BUCKET>/customer_aggregation/'
TBLPROPERTIES ('skip.header.line.count'='1');


-- STEP 2: Managed Parquet table
CREATE TABLE IF NOT EXISTS cai_sdx_se_indonesia.customer_aggregation (
    cif                 STRING         COMMENT 'Customer Identification',
    no_rekening         STRING         COMMENT 'Nomor rekening',
    jenis               STRING         COMMENT 'Jenis nasabah: Perorangan / Badan Usaha',
    name                STRING         COMMENT 'Nama nasabah',
    cabang              STRING         COMMENT 'Kode cabang',
    jenis_rekening      STRING         COMMENT 'Tabungan / Giro / Deposito',
    name_cabang         STRING         COMMENT 'Nama cabang',
    min_saldo           DECIMAL(20,2)  COMMENT 'Saldo minimum periode',
    saldo_t0            DECIMAL(20,2)  COMMENT 'Saldo pada periode t0',
    tgl_trx_terakhir    DATE           COMMENT 'Tanggal transaksi terakhir',
    total_tx            INT            COMMENT 'Total transaksi',
    tx_sistem           INT            COMMENT 'Transaksi sistem/auto',
    tx_nasabah          INT            COMMENT 'Transaksi yang dilakukan nasabah',
    count_tx_kredit     INT            COMMENT 'Jumlah transaksi kredit',
    avg_nominal_kredit  DECIMAL(20,2)  COMMENT 'Rata-rata nominal kredit',
    max_nominal_kredit  DECIMAL(20,2)  COMMENT 'Nominal kredit tertinggi',
    min_nominal_kredit  DECIMAL(20,2)  COMMENT 'Nominal kredit terendah',
    std_nominal_kredit  DECIMAL(20,2)  COMMENT 'Std dev nominal kredit',
    count_tx_debit      INT            COMMENT 'Jumlah transaksi debit',
    avg_nominal_debit   DECIMAL(20,2)  COMMENT 'Rata-rata nominal debit',
    max_nominal_debit   DECIMAL(20,2)  COMMENT 'Nominal debit tertinggi',
    min_nominal_debit   DECIMAL(20,2)  COMMENT 'Nominal debit terendah',
    std_nominal_debit   DECIMAL(20,2)  COMMENT 'Std dev nominal debit',
    has_tx_first_6m     BOOLEAN        COMMENT 'Ada transaksi di 6 bulan pertama periode',
    has_tx_last_6m      BOOLEAN        COMMENT 'Ada transaksi di 6 bulan terakhir periode',
    saldo_end_target    DECIMAL(20,2)  COMMENT 'Target saldo akhir periode',
    status_rekening     TINYINT        COMMENT '0=Aktif, 1=Dormant, 2=Tutup',
    t0                  DATE           COMMENT 'Reference date periode'
)
STORED AS PARQUET;


-- STEP 3: INSERT with type casts
INSERT INTO cai_sdx_se_indonesia.customer_aggregation
SELECT
    cif,
    no_rekening,
    jenis,
    name,
    cabang,
    jenis_rekening,
    name_cabang,
    CAST(min_saldo           AS DECIMAL(20,2)),
    CAST(saldo_t0            AS DECIMAL(20,2)),
    CAST(tgl_trx_terakhir    AS DATE),
    CAST(total_tx            AS INT),
    CAST(tx_sistem           AS INT),
    CAST(tx_nasabah          AS INT),
    CAST(count_tx_kredit     AS INT),
    CAST(avg_nominal_kredit  AS DECIMAL(20,2)),
    CAST(max_nominal_kredit  AS DECIMAL(20,2)),
    CAST(min_nominal_kredit  AS DECIMAL(20,2)),
    CAST(std_nominal_kredit  AS DECIMAL(20,2)),
    CAST(count_tx_debit      AS INT),
    CAST(avg_nominal_debit   AS DECIMAL(20,2)),
    CAST(max_nominal_debit   AS DECIMAL(20,2)),
    CAST(min_nominal_debit   AS DECIMAL(20,2)),
    CAST(std_nominal_debit   AS DECIMAL(20,2)),
    CASE WHEN UPPER(has_tx_first_6m) = 'TRUE' THEN TRUE ELSE FALSE END,
    CASE WHEN UPPER(has_tx_last_6m)  = 'TRUE' THEN TRUE ELSE FALSE END,
    CAST(saldo_end_target    AS DECIMAL(20,2)),
    CAST(status_rekening     AS TINYINT),
    CAST(t0                  AS DATE)
FROM cai_sdx_se_indonesia.customer_aggregation_staging;


-- STEP 4: Drop staging table
DROP TABLE IF EXISTS cai_sdx_se_indonesia.customer_aggregation_staging;


-- STEP 5: Sanity check
SELECT
    COUNT(*)                                    AS total_rows,
    COUNT(DISTINCT cif)                         AS unique_cif,
    COUNT(DISTINCT no_rekening)                 AS unique_rekening,
    SUM(CASE WHEN status_rekening = 0 THEN 1 ELSE 0 END) AS aktif,
    SUM(CASE WHEN status_rekening = 1 THEN 1 ELSE 0 END) AS dormant,
    SUM(CASE WHEN status_rekening = 2 THEN 1 ELSE 0 END) AS tutup,
    AVG(saldo_t0)                               AS avg_saldo_t0,
    AVG(total_tx)                               AS avg_total_tx
FROM cai_sdx_se_indonesia.customer_aggregation;
