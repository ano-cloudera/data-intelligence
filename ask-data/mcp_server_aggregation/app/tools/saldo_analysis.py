from __future__ import annotations

from typing import Any

from app.impala_client import execute_query, qualified_table


def run_saldo_analysis(
    jenis_rekening: str | None = None,
    status_rekening: int | None = None,
) -> dict[str, Any]:
    table = qualified_table()
    conditions: list[str] = []

    if jenis_rekening:
        safe_jr = jenis_rekening.replace("'", "''")
        conditions.append(f"jenis_rekening = '{safe_jr}'")
    if status_rekening is not None:
        conditions.append(f"status_rekening = {int(status_rekening)}")

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    sql = f"""
SELECT
    jenis_rekening,
    status_label,
    COUNT(*) AS jumlah_rekening,
    ROUND(AVG(saldo_t0), 2) AS avg_saldo,
    ROUND(MIN(saldo_t0), 2) AS min_saldo,
    ROUND(MAX(saldo_t0), 2) AS max_saldo,
    ROUND(AVG(total_tx), 2) AS avg_total_transaksi,
    ROUND(AVG(rasio_kredit), 4) AS avg_rasio_kredit,
    ROUND(AVG(hari_sejak_trx), 0) AS avg_hari_sejak_trx,
    SUM(CASE WHEN hari_sejak_trx <= 180 THEN 1 ELSE 0 END) AS rekening_aktif_180hr,
    SUM(CASE WHEN hari_sejak_trx > 180 THEN 1 ELSE 0 END) AS rekening_tidak_aktif_180hr
FROM {table}
{where}
GROUP BY jenis_rekening, status_rekening, status_label
ORDER BY jenis_rekening, status_rekening
LIMIT 30
""".strip()

    try:
        return execute_query(sql)
    except Exception as exc:
        return {"error": str(exc)}
