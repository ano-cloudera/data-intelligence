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
    SUM(CASE WHEN hari_sejak_trx <= 30 THEN 1 ELSE 0 END) AS aktif_30hr,
    SUM(CASE WHEN hari_sejak_trx BETWEEN 31 AND 180 THEN 1 ELSE 0 END) AS kurang_aktif,
    SUM(CASE WHEN hari_sejak_trx > 180 THEN 1 ELSE 0 END) AS tidak_aktif_180hr,
    ROUND(AVG(hari_sejak_trx), 0) AS avg_hari_sejak_trx,
    ROUND(SUM(CASE WHEN hari_sejak_trx > 180 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS pct_tidak_aktif
FROM {table}
{where}
GROUP BY jenis_rekening
ORDER BY tidak_aktif_180hr DESC
LIMIT 20
""".strip()

    try:
        return execute_query(sql)
    except Exception as exc:
        return {"error": str(exc)}
