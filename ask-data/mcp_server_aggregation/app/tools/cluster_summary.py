from __future__ import annotations

from typing import Any

from app.impala_client import execute_query, qualified_table


def run_cluster_summary() -> dict[str, Any]:
    """Return ringkasan per cluster: jumlah, avg saldo, avg transaksi, RFM breakdown."""
    table = qualified_table()

    sql = f"""
SELECT
    cluster_label,
    COUNT(*) AS total_rekening,
    SUM(CASE WHEN status_rekening = 0 THEN 1 ELSE 0 END) AS aktif,
    SUM(CASE WHEN status_rekening = 1 THEN 1 ELSE 0 END) AS dormant,
    ROUND(AVG(saldo_t0), 0) AS avg_saldo,
    ROUND(AVG(total_tx), 1) AS avg_transaksi,
    ROUND(AVG(hari_sejak_trx), 0) AS avg_hari_sejak_trx,
    ROUND(AVG(rfm_score), 1) AS avg_rfm_score
FROM {table}
GROUP BY cluster_label
ORDER BY cluster_label
""".strip()

    try:
        return execute_query(sql)
    except Exception as exc:
        return {"error": str(exc)}
