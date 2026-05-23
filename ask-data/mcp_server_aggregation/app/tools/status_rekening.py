from __future__ import annotations

from typing import Any

from app.impala_client import execute_query, qualified_table


def run_status_rekening_distribution(
    jenis_rekening: str | None = None,
    cabang: str | None = None,
) -> dict[str, Any]:
    table = qualified_table()
    conditions: list[str] = []

    if jenis_rekening:
        safe_jr = jenis_rekening.replace("'", "''")
        conditions.append(f"jenis_rekening = '{safe_jr}'")
    if cabang:
        safe_cabang = cabang.replace("'", "''")
        conditions.append(f"cabang = '{safe_cabang}'")

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    sql = f"""
SELECT
    status_label,
    jenis_rekening,
    cabang,
    COUNT(*) AS jumlah_rekening,
    ROUND(AVG(saldo_t0), 0) AS avg_saldo,
    ROUND(AVG(hari_sejak_trx), 0) AS avg_hari_sejak_trx
FROM {table}
{where}
GROUP BY status_rekening, status_label, jenis_rekening, cabang
ORDER BY status_rekening, jenis_rekening, cabang
LIMIT 30
""".strip()

    try:
        return execute_query(sql)
    except Exception as exc:
        return {"error": str(exc)}
