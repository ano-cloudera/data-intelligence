from __future__ import annotations

from typing import Any

from app.impala_client import execute_query, qualified_table


def run_rekening_summary(
    cif: str | None = None,
    jenis_rekening: str | None = None,
    limit: int = 20,
    status_rekening: int | None = None,
) -> dict[str, Any]:
    table = qualified_table()
    conditions: list[str] = []

    if cif:
        safe_cif = cif.replace("'", "''")
        conditions.append(f"cif = '{safe_cif}'")
    if jenis_rekening:
        safe_jr = jenis_rekening.replace("'", "''")
        conditions.append(f"jenis_rekening = '{safe_jr}'")
    if status_rekening is not None:
        conditions.append(f"status_rekening = {int(status_rekening)}")

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    limit = max(1, min(int(limit), 100))

    sql = f"""
SELECT
    cabang,
    jenis,
    jenis_rekening,
    status_label,
    cluster_label,
    rfm_segment,
    saldo_segment,
    activity_level,
    age_group,
    jenis_kelamin_label,
    COUNT(*) AS total_rekening,
    ROUND(SUM(saldo_t0), 2) AS total_saldo,
    ROUND(AVG(saldo_t0), 2) AS avg_saldo,
    ROUND(AVG(total_tx), 1) AS avg_transaksi,
    ROUND(AVG(hari_sejak_trx), 0) AS avg_hari_sejak_trx,
    ROUND(AVG(rfm_score), 1) AS avg_rfm_score
FROM {table}
{where}
GROUP BY cabang, jenis, jenis_rekening, status_label, cluster_label,
         rfm_segment, saldo_segment, activity_level, age_group, jenis_kelamin_label
ORDER BY total_saldo DESC
LIMIT {limit}
""".strip()

    try:
        return execute_query(sql)
    except Exception as exc:
        return {"error": str(exc)}
