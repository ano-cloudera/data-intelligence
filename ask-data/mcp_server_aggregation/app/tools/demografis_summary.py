from __future__ import annotations

from typing import Any

from app.impala_client import execute_query, qualified_table


def run_demografis_summary() -> dict[str, Any]:
    """Return distribusi demografis: gender, age group, activity level."""
    table = qualified_table()

    sql = f"""
SELECT
    jenis_kelamin_label,
    age_group,
    activity_level,
    COUNT(*) AS total_rekening,
    ROUND(AVG(saldo_t0), 0) AS avg_saldo,
    ROUND(AVG(total_tx), 1) AS avg_transaksi,
    ROUND(AVG(hari_sejak_trx), 0) AS avg_hari_sejak_trx
FROM {table}
GROUP BY jenis_kelamin_label, age_group, activity_level
ORDER BY jenis_kelamin_label, age_group, activity_level
LIMIT 30
""".strip()

    try:
        return execute_query(sql)
    except Exception as exc:
        return {"error": str(exc)}
