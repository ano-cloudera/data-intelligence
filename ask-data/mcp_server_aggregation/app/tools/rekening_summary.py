from __future__ import annotations

from typing import Any

from app.impala_client import execute_query, qualified_table


def run_rekening_summary(
    cif: str | None = None,
    jenis_rekening: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    table = qualified_table()
    conditions: list[str] = []

    if cif:
        safe_cif = cif.replace("'", "''")
        conditions.append(f"cif = '{safe_cif}'")
    if jenis_rekening:
        safe_jr = jenis_rekening.replace("'", "''")
        conditions.append(f"jenis_rekening = '{safe_jr}'")

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    sql = f"""
SELECT
    cif,
    name,
    jenis,
    cabang,
    name_cabang,
    COUNT(no_rekening) AS total_rekening,
    jenis_rekening,
    SUM(saldo_t0) AS total_saldo_t0,
    SUM(saldo_end_target) AS total_saldo_end_target,
    SUM(total_tx) AS total_transaksi,
    MAX(tgl_trx_terakhir) AS tgl_trx_terakhir,
    status_rekening
FROM {table}
{where}
GROUP BY cif, name, jenis, cabang, name_cabang, jenis_rekening, status_rekening
ORDER BY total_saldo_t0 DESC
LIMIT {limit}
""".strip()

    try:
        return execute_query(sql)
    except Exception as exc:
        return {"error": str(exc)}
