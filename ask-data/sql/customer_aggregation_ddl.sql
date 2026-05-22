DROP TABLE cai_sdx_se_indonesia.customer_aggregation_staging ; 

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
LOCATION 's3a://go01-demo/user/cai-demo-se-indonesia/data/customer segmentation aggregation'
TBLPROPERTIES ('skip.header.line.count'='1');



select * FROM customer_aggregation_staging ; 