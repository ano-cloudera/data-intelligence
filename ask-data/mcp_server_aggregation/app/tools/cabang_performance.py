from __future__ import annotations

from typing import Any

from app.impala_client import execute_query, qualified_table


def run_cabang_performance() -> dict[str, Any]:
    table = qualified_table()
    sql = f"""
SELECT
    cabang,
    name_cabang,
    COUNT(*) AS total_rekening,
    SUM(CASE WHEN status_rekening = '0' THEN 1 ELSE 0 END) AS aktif,
    SUM(CASE WHEN status_rekening = '1' THEN 1 ELSE 0 END) AS dormant,
    SUM(CASE WHEN status_rekening = '2' THEN 1 ELSE 0 END) AS tutup,
    ROUND(SUM(CASE WHEN status_rekening = '1' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS pct_dormant,
    ROUND(AVG(CAST(saldo_t0 AS DECIMAL(20,2))), 0) AS avg_saldo,
    ROUND(AVG(CAST(total_tx AS INT)), 1) AS avg_transaksi,
    SUM(CASE WHEN UPPER(has_tx_last_6m) = 'FALSE' THEN 1 ELSE 0 END) AS tidak_aktif_6m
FROM {table}
GROUP BY cabang, name_cabang
ORDER BY dormant DESC, total_rekening DESC
""".strip()

    try:
        return execute_query(sql)
    except Exception as exc:
        return {"error": str(exc)}
