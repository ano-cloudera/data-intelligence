from __future__ import annotations

import concurrent.futures
from typing import Any

from app.impala_client import execute_query, qualified_table


def _build_queries(table: str) -> dict[str, str]:
    return {
        "status_summary": f"""
            SELECT
                status_label AS status,
                COUNT(*) AS jumlah,
                ROUND(AVG(saldo_t0), 0) AS avg_saldo
            FROM {table}
            GROUP BY status_rekening, status_label
            ORDER BY status_rekening
        """,
        "cluster_summary": f"""
            SELECT
                cluster_label,
                COUNT(*) AS total,
                SUM(CASE WHEN status_rekening = 0 THEN 1 ELSE 0 END) AS aktif,
                SUM(CASE WHEN status_rekening = 1 THEN 1 ELSE 0 END) AS dormant,
                ROUND(AVG(saldo_t0), 0) AS avg_saldo,
                ROUND(AVG(hari_sejak_trx), 0) AS avg_hari_sejak_trx
            FROM {table}
            GROUP BY cluster_label
            ORDER BY cluster_label
        """,
        "rfm_summary": f"""
            SELECT
                rfm_segment,
                COUNT(*) AS jumlah,
                ROUND(AVG(saldo_t0), 0) AS avg_saldo,
                ROUND(AVG(rfm_score), 1) AS avg_rfm_score
            FROM {table}
            GROUP BY rfm_segment
            ORDER BY avg_rfm_score DESC
        """,
        "top3_cabang_saldo": f"""
            SELECT
                cabang,
                COUNT(*) AS total_rekening,
                ROUND(AVG(saldo_t0), 0) AS avg_saldo,
                ROUND(AVG(hari_sejak_trx), 0) AS avg_hari_sejak_trx
            FROM {table}
            GROUP BY cabang
            ORDER BY avg_saldo DESC
            LIMIT 3
        """,
    }


SECTION_LABELS = {
    "status_summary":   "[ Status Rekening (Aktif/Dormant/Tutup) ]",
    "cluster_summary":  "[ Segmen Nasabah (Cluster K-Means) ]",
    "rfm_summary":      "[ RFM Segment (Champions/Loyal/Potential/At Risk/Lost) ]",
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

    lines = ["=== QUICK STATS - Customer Segments ===\n"]
    for label in queries:
        lines.append(_format_section(label, results.get(label, Exception("No result"))))

    return {"summary": "\n".join(lines)}
