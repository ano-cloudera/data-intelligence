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
    status_rekening,
    COUNT(*) AS jumlah_rekening,
    ROUND(AVG(saldo_t0), 2) AS avg_saldo_t0,
    ROUND(MIN(saldo_t0), 2) AS min_saldo_t0,
    ROUND(MAX(saldo_t0), 2) AS max_saldo_t0,
    ROUND(AVG(min_saldo), 2) AS avg_saldo_minimum,
    ROUND(AVG(total_tx), 2) AS avg_total_transaksi,
    ROUND(AVG(count_tx_kredit), 2) AS avg_tx_kredit,
    ROUND(AVG(avg_nominal_kredit), 2) AS avg_nominal_kredit,
    ROUND(AVG(count_tx_debit), 2) AS avg_tx_debit,
    ROUND(AVG(avg_nominal_debit), 2) AS avg_nominal_debit,
    SUM(CASE WHEN has_tx_last_6m = true THEN 1 ELSE 0 END) AS rekening_aktif_6m,
    SUM(CASE WHEN has_tx_last_6m = false THEN 1 ELSE 0 END) AS rekening_tidak_aktif_6m
FROM {table}
{where}
GROUP BY jenis_rekening, status_rekening
ORDER BY jenis_rekening, status_rekening
""".strip()

    try:
        return execute_query(sql)
    except Exception as exc:
        return {"error": str(exc)}
