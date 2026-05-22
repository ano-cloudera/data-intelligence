from __future__ import annotations

from typing import Any

from app.impala_client import execute_query, qualified_table


def run_transaksi_trend(jenis_rekening: str | None = None) -> dict[str, Any]:
    table = qualified_table()
    conditions = []
    if jenis_rekening:
        safe = jenis_rekening.replace("'", "''")
        conditions.append(f"jenis_rekening = '{safe}'")
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    sql = f"""
SELECT
    jenis_rekening,
    COUNT(*) AS total_rekening,
    SUM(CASE WHEN UPPER(has_tx_last_6m) = 'TRUE'  THEN 1 ELSE 0 END) AS aktif_6m_terakhir,
    SUM(CASE WHEN UPPER(has_tx_last_6m) = 'FALSE' THEN 1 ELSE 0 END) AS tidak_aktif_6m_terakhir,
    SUM(CASE WHEN UPPER(has_tx_first_6m) = 'TRUE' AND UPPER(has_tx_last_6m) = 'FALSE' THEN 1 ELSE 0 END) AS baru_dormant,
    SUM(CASE WHEN UPPER(has_tx_first_6m) = 'FALSE' AND UPPER(has_tx_last_6m) = 'FALSE' THEN 1 ELSE 0 END) AS dormant_lama,
    SUM(CASE WHEN status_rekening = '1' THEN 1 ELSE 0 END) AS status_dormant,
    ROUND(SUM(CASE WHEN UPPER(has_tx_last_6m) = 'FALSE' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS pct_tidak_aktif
FROM {table}
{where}
GROUP BY jenis_rekening
ORDER BY tidak_aktif_6m_terakhir DESC
""".strip()

    try:
        return execute_query(sql)
    except Exception as exc:
        return {"error": str(exc)}
