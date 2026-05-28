from __future__ import annotations

from typing import Any

from app.impala_client import execute_query, qualified_table


def run_cluster_summary(cluster_label: str | None = None) -> dict[str, Any]:
    """Return ringkasan per cluster: jumlah, avg saldo, avg transaksi, RFM breakdown."""
    table = qualified_table()

    conditions = []
    if cluster_label:
        safe = cluster_label.replace("'", "''")
        conditions.append(f"cluster_label = '{safe}'")
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    sql = f"""
SELECT
    cluster_label,
    COUNT(*) AS total_rekening,
    SUM(CASE WHEN status_rekening = 0 THEN 1 ELSE 0 END) AS aktif,
    SUM(CASE WHEN status_rekening = 1 THEN 1 ELSE 0 END) AS dormant,
    SUM(CASE WHEN status_rekening = 2 THEN 1 ELSE 0 END) AS tutup,
    ROUND(AVG(saldo_t0), 0) AS avg_saldo,
    ROUND(MIN(saldo_t0), 0) AS min_saldo,
    ROUND(MAX(saldo_t0), 0) AS max_saldo,
    ROUND(AVG(total_tx), 1) AS avg_transaksi,
    ROUND(AVG(hari_sejak_trx), 0) AS avg_hari_sejak_trx,
    ROUND(AVG(rfm_score), 1) AS avg_rfm_score,
    ROUND(AVG(umur), 1) AS avg_umur,
    SUM(CASE WHEN jenis_kelamin_label = 'Pria' THEN 1 ELSE 0 END) AS pria,
    SUM(CASE WHEN jenis_kelamin_label = 'Wanita' THEN 1 ELSE 0 END) AS wanita
FROM {table}
{where}
GROUP BY cluster_label
ORDER BY cluster_label
""".strip()

    try:
        return execute_query(sql)
    except Exception as exc:
        return {"error": str(exc)}
