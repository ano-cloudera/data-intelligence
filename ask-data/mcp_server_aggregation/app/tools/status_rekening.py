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
    status_rekening,
    CASE CAST(status_rekening AS INT)
        WHEN 0 THEN 'Aktif'
        WHEN 1 THEN 'Dormant'
        WHEN 2 THEN 'Tutup'
        ELSE 'Tidak Diketahui'
    END AS status_label,
    jenis_rekening,
    cabang,
    name_cabang,
    COUNT(*) AS jumlah_rekening,
    ROUND(AVG(CAST(saldo_t0 AS DECIMAL(20,2))), 2) AS avg_saldo,
    SUM(CASE WHEN UPPER(has_tx_last_6m) = 'TRUE' THEN 1 ELSE 0 END) AS aktif_6m,
    SUM(CASE WHEN UPPER(has_tx_first_6m) = 'TRUE' THEN 1 ELSE 0 END) AS aktif_awal_6m
FROM {table}
{where}
GROUP BY status_rekening, jenis_rekening, cabang, name_cabang
ORDER BY status_rekening, jenis_rekening, cabang
""".strip()

    try:
        return execute_query(sql)
    except Exception as exc:
        return {"error": str(exc)}
