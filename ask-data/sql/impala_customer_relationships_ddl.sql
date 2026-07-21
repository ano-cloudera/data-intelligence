-- =============================================================
-- customer_relationships — Impala External Table DDL
-- Bank XYZ Demo — Risk Propagation Graph Edges
-- Regenerated: 2026-07-21
--
-- Graph edges antar nasabah untuk fraud/delinquency propagation demo.
-- IDs (customer_id / related_customer_id) are `cif` values from
-- customer_segments_staging — same table domain_config.yaml points to,
-- so the graph endpoint can join back for credit_score/churn/lat/lng.
-- Relationship types:
--   co_borrower    : joint policy / shared loan (risk_weight 0.70–0.95)
--   guarantor      : one customer guarantees another (risk_weight 0.80–0.99)
--   same_employer  : same branch + age group proxy (risk_weight 0.30–0.60)
--   same_branch    : same branch registration (risk_weight 0.10–0.35)
-- =============================================================

DROP TABLE IF EXISTS cai_sdx_se_indonesia.customer_relationships;

CREATE EXTERNAL TABLE cai_sdx_se_indonesia.customer_relationships (
    customer_id             STRING      COMMENT 'Source customer cif. FK to customer_segments_staging.cif',
    related_customer_id     STRING      COMMENT 'Target customer cif. FK to customer_segments_staging.cif',
    relationship_type       STRING      COMMENT 'co_borrower / guarantor / same_employer / same_branch',
    risk_weight             DOUBLE      COMMENT 'Risk propagation strength. Range 0–1. Higher = stronger contagion',
    is_active               STRING      COMMENT 'true / false — whether the relationship is currently active'
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
STORED AS TEXTFILE
LOCATION 's3a://go01-demo/user/cai-demo-se-indonesia/data/customer_relationships'
TBLPROPERTIES ('skip.header.line.count'='1');

INVALIDATE METADATA cai_sdx_se_indonesia.customer_relationships;
COMPUTE STATS cai_sdx_se_indonesia.customer_relationships;

-- Validation
SELECT COUNT(*) AS total_edges FROM cai_sdx_se_indonesia.customer_relationships;

SELECT
    relationship_type,
    COUNT(*)                    AS edge_count,
    ROUND(AVG(risk_weight), 3)  AS avg_risk_weight,
    SUM(CASE WHEN is_active = 'true' THEN 1 ELSE 0 END) AS active_edges
FROM cai_sdx_se_indonesia.customer_relationships
GROUP BY relationship_type
ORDER BY edge_count DESC;
