from __future__ import annotations

from typing import Any

from app.impala_client import execute_query, qualified_table


VALID_ORDER_BY = {
    "dormant": "dormant DESC, total_rekening DESC",
    "avg_saldo": "avg_saldo DESC",
    "total_rekening": "total_rekening DESC",
    "tidak_aktif": "tidak_aktif_180hr DESC",
    "pct_dormant": "pct_dormant DESC",
}


def run_cabang_performance(
    order_by: str = "dormant",
    limit: int = 10,
) -> dict[str, Any]:
    table = qualified_table()
    order_clause = VALID_ORDER_BY.get(order_by, VALID_ORDER_BY["dormant"])
    limit = max(1, min(int(limit), 50))

    sql = f"""
SELECT
    cabang,
    COUNT(*) AS total_rekening,
    SUM(CASE WHEN status_rekening = 0 THEN 1 ELSE 0 END) AS aktif,
    SUM(CASE WHEN status_rekening = 1 THEN 1 ELSE 0 END) AS dormant,
    SUM(CASE WHEN status_rekening = 2 THEN 1 ELSE 0 END) AS tutup,
    ROUND(SUM(CASE WHEN status_rekening = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS pct_dormant,
    ROUND(AVG(saldo_t0), 0) AS avg_saldo,
    ROUND(AVG(total_tx), 1) AS avg_transaksi,
    ROUND(AVG(hari_sejak_trx), 0) AS avg_hari_sejak_trx,
    SUM(CASE WHEN hari_sejak_trx > 180 THEN 1 ELSE 0 END) AS tidak_aktif_180hr
FROM {table}
GROUP BY cabang
ORDER BY {order_clause}
LIMIT {limit}
""".strip()

    try:
        return execute_query(sql)
    except Exception as exc:
        return {"error": str(exc)}
