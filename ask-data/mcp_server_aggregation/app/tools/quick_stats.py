from __future__ import annotations

import concurrent.futures
from typing import Any

from app.impala_client import execute_query, qualified_table


def _build_queries(table: str) -> dict[str, str]:
    return {
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


SECTION_LABELS = {
    "status_summary":   "[ Status Rekening (Aktif/Dormant/Tutup) ]",
    "jenis_summary":    "[ Jenis Rekening (Tabungan/Giro/Deposito) ]",
    "tidak_aktif_6m":   "[ Rekening Tidak Aktif 6 Bulan ]",
    "top3_cabang_saldo":"[ Top 3 Cabang - Rata-rata Saldo Tertinggi ]",
}


def _format_section(label: str, result: dict[str, Any] | Exception) -> str:
    title = SECTION_LABELS.get(label, label)
    lines = [title]
    if isinstance(result, Exception):
        lines.append(f"ERROR: {result}\n")
        return "\n".join(lines)
    rows = result.get("rows", [])
    if not rows:
        lines.append("Tidak ada data.\n")
        return "\n".join(lines)
    cols = list(rows[0].keys())
    col_widths = {c: max(len(c), max(len(str(row.get(c, ""))) for row in rows)) for c in cols}
    lines.append("  ".join(c.upper().ljust(col_widths[c]) for c in cols))
    lines.append("  ".join("-" * col_widths[c] for c in cols))
    for row in rows:
        lines.append("  ".join(str(row.get(c, "")).ljust(col_widths[c]) for c in cols))
    lines.append("")
    return "\n".join(lines)


def run_quick_stats() -> dict[str, Any]:
    """Run all 4 overview queries in parallel, return combined summary."""
    table = qualified_table()
    queries = _build_queries(table)

    results: dict[str, Any] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(execute_query, sql.strip()): label for label, sql in queries.items()}
        for future in concurrent.futures.as_completed(futures):
            label = futures[future]
            try:
                results[label] = future.result()
            except Exception as exc:
                results[label] = exc

    lines = ["=== QUICK STATS - Customer Aggregation ===\n"]
    for label in queries:  # preserve order
        lines.append(_format_section(label, results.get(label, Exception("No result"))))

    return {"summary": "\n".join(lines)}
