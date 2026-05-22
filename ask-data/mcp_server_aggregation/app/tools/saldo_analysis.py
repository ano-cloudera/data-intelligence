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
        conditions.append(f"CAST(status_rekening AS INT) = {int(status_rekening)}")

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    sql = f"""
SELECT
    jenis_rekening,
    status_rekening,
    COUNT(*) AS jumlah_rekening,
    ROUND(AVG(CAST(saldo_t0 AS DECIMAL(20,2))), 2) AS avg_saldo_t0,
    ROUND(MIN(CAST(saldo_t0 AS DECIMAL(20,2))), 2) AS min_saldo_t0,
    ROUND(MAX(CAST(saldo_t0 AS DECIMAL(20,2))), 2) AS max_saldo_t0,
    ROUND(AVG(CAST(min_saldo AS DECIMAL(20,2))), 2) AS avg_saldo_minimum,
    ROUND(AVG(CAST(total_tx AS INT)), 2) AS avg_total_transaksi,
    ROUND(AVG(CAST(count_tx_kredit AS INT)), 2) AS avg_tx_kredit,
    ROUND(AVG(CAST(avg_nominal_kredit AS DECIMAL(20,2))), 2) AS avg_nominal_kredit,
    ROUND(AVG(CAST(count_tx_debit AS INT)), 2) AS avg_tx_debit,
    ROUND(AVG(CAST(avg_nominal_debit AS DECIMAL(20,2))), 2) AS avg_nominal_debit,
    SUM(CASE WHEN UPPER(has_tx_last_6m) = 'TRUE' THEN 1 ELSE 0 END) AS rekening_aktif_6m,
    SUM(CASE WHEN UPPER(has_tx_last_6m) = 'FALSE' THEN 1 ELSE 0 END) AS rekening_tidak_aktif_6m
FROM {table}
{where}
GROUP BY jenis_rekening, status_rekening
ORDER BY jenis_rekening, status_rekening
""".strip()

    try:
        return execute_query(sql)
    except Exception as exc:
        return {"error": str(exc)}
