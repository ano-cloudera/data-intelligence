from __future__ import annotations

from typing import Any

from app.impala_client import execute_query, qualified_table


def run_quick_stats() -> dict[str, Any]:
    """Single call — return semua overview penting sekaligus."""
    table = qualified_table()

    queries = {
        "status_summary": f"""
            SELECT
                CASE status_rekening
                    WHEN '0' THEN 'Aktif'
                    WHEN '1' THEN 'Dormant'
                    WHEN '2' THEN 'Tutup'
                    ELSE 'Lainnya'
                END AS status,
                COUNT(*) AS jumlah,
                ROUND(AVG(CAST(saldo_t0 AS DECIMAL(20,2))), 0) AS avg_saldo
            FROM {table}
            GROUP BY status_rekening
            ORDER BY status_rekening
        """,
        "jenis_summary": f"""
            SELECT
                jenis_rekening,
                COUNT(*) AS total,
                SUM(CASE WHEN status_rekening = '0' THEN 1 ELSE 0 END) AS aktif,
                SUM(CASE WHEN status_rekening = '1' THEN 1 ELSE 0 END) AS dormant,
                ROUND(AVG(CAST(saldo_t0 AS DECIMAL(20,2))), 0) AS avg_saldo
            FROM {table}
            GROUP BY jenis_rekening
            ORDER BY jenis_rekening
        """,
        "tidak_aktif_6m": f"""
            SELECT
                jenis_rekening,
                SUM(CASE WHEN UPPER(has_tx_last_6m) = 'FALSE' THEN 1 ELSE 0 END) AS tidak_aktif_6m,
                COUNT(*) AS total,
                ROUND(SUM(CASE WHEN UPPER(has_tx_last_6m) = 'FALSE' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS pct
            FROM {table}
            GROUP BY jenis_rekening
        """,
        "top3_cabang_saldo": f"""
            SELECT cabang, name_cabang,
                COUNT(*) AS total_rekening,
                ROUND(AVG(CAST(saldo_t0 AS DECIMAL(20,2))), 0) AS avg_saldo
            FROM {table}
            GROUP BY cabang, name_cabang
            ORDER BY avg_saldo DESC
            LIMIT 3
        """,
    }

    lines = ["=== QUICK STATS — Customer Aggregation ===\n"]

    for label, sql in queries.items():
        try:
            result = execute_query(sql.strip())
            rows = result.get("rows", [])
            if not rows:
                lines.append(f"[{label}]: tidak ada data\n")
                continue
            cols = list(rows[0].keys())
            lines.append(f"[{label}]")
            lines.append(" | ".join(cols))
            lines.append("-" * 60)
            for row in rows:
                lines.append(" | ".join(str(row.get(c, "")) for c in cols))
            lines.append("")
        except Exception as exc:
            lines.append(f"[{label}] ERROR: {exc}\n")

    return {"summary": "\n".join(lines)}
