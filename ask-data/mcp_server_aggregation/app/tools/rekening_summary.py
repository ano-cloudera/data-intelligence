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
        conditions.append(f"CAST(status_rekening AS INT) = {int(status_rekening)}")

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    limit = max(1, min(int(limit), 100))

    sql = f"""
SELECT
    cif,
    name,
    jenis_rekening,
    cabang,
    name_cabang,
    status_rekening,
    COUNT(no_rekening) AS total_rekening,
    ROUND(SUM(CAST(saldo_t0 AS DECIMAL(20,2))), 2) AS total_saldo,
    SUM(CAST(total_tx AS INT)) AS total_transaksi,
    SUM(CAST(count_tx_kredit AS INT)) AS total_tx_kredit,
    ROUND(AVG(CAST(avg_nominal_kredit AS DECIMAL(20,2))), 2) AS avg_nominal_kredit,
    SUM(CAST(count_tx_debit AS INT)) AS total_tx_debit,
    ROUND(AVG(CAST(avg_nominal_debit AS DECIMAL(20,2))), 2) AS avg_nominal_debit,
    MAX(tgl_trx_terakhir) AS tgl_trx_terakhir
FROM {table}
{where}
GROUP BY cif, name, jenis_rekening, cabang, name_cabang, status_rekening
ORDER BY total_saldo DESC
LIMIT {limit}
""".strip()

    try:
        return execute_query(sql)
    except Exception as exc:
        return {"error": str(exc)}
