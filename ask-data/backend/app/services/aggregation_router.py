from __future__ import annotations

import re


GEO_MARKERS = (
    "peta", "map", "geografis", "wilayah", "sebaran", "persebaran",
    "visualisasi cabang", "tampilkan di peta", "pada peta",
    "lokasi cabang", "di mana cabang",
)


def is_map_request(question: str) -> bool:
    q = question.lower()
    return any(marker in q for marker in GEO_MARKERS)


def resolve_aggregation_tool(question: str) -> tuple[str, dict]:
    """Map pertanyaan natural language ke MCP tool + params yang tepat."""
    q = question.lower().strip()

    # map / geospatial — prioritas tertinggi
    if is_map_request(q):
        metric = "total"
        limit = 50
        if "dormant" in q:
            metric = "dormant"
        elif "saldo" in q:
            metric = "avg_saldo"
        elif "persen" in q or "%" in q:
            metric = "pct_dormant"
        m = re.search(r"top\s*(\d+)", q)
        if m:
            limit = int(m.group(1))
        return "cabang_map", {"metric": metric, "limit": limit}

    # cluster spesifik
    if "young syariah digital" in q:
        return "cluster_summary", {"cluster_label": "Young Syariah Digital"}
    if "silent mature" in q:
        return "cluster_summary", {"cluster_label": "Silent Mature"}
    if "konvensional produktif" in q:
        return "cluster_summary", {"cluster_label": "Konvensional Produktif"}

    # demografis
    if any(k in q for k in ("gender", "usia", "kelompok usia", "age group", "pria", "wanita", "laki", "perempuan", "demografis")):
        return "demografis_summary", {}

    # cabang
    if any(k in q for k in ("cabang", "performa cabang", "ranking cabang", "top cabang")):
        order_by = "avg_saldo"
        limit = 10
        if "dormant" in q:
            order_by = "dormant"
        elif "tidak aktif" in q:
            order_by = "tidak_aktif"
        m = re.search(r"top\s*(\d+)", q)
        if m:
            limit = int(m.group(1))
        return "cabang_performance", {"order_by": order_by, "limit": limit}

    # saldo
    if any(k in q for k in ("saldo", "rata-rata saldo", "avg saldo")):
        if "dormant" in q:
            return "saldo_analysis", {"status_rekening": 1}
        if "tutup" in q:
            return "saldo_analysis", {"status_rekening": 2}
        return "saldo_analysis", {}

    # transaksi trend
    if any(k in q for k in ("transaksi", "tren aktivitas", "aktivitas per jenis", "tidak aktif per jenis")):
        return "transaksi_trend", {}

    # status distribusi
    if any(k in q for k in ("distribusi status", "rekening aktif", "rekening dormant", "distribusi rekening")):
        return "status_rekening_distribution", {}

    # cluster perbandingan / semua cluster
    if any(k in q for k in ("cluster", "segmentasi", "segmen nasabah", "rfm")):
        return "cluster_summary", {}

    # default: quick_stats
    return "quick_stats", {}


def format_aggregation_answer(tool: str, result: dict) -> str:
    """Format hasil aggregation tool menjadi jawaban yang readable."""
    if "error" in result:
        return f"Maaf, terjadi kesalahan saat mengambil data: {result['error']}"

    # Map tool: result has 'features' not 'rows'
    if tool == "cabang_map":
        features = result.get("features", [])
        n = len(features)
        metric = result.get("metric", "total")
        metric_label = {
            "total": "total rekening",
            "dormant": "rekening dormant",
            "avg_saldo": "rata-rata saldo",
            "pct_dormant": "% dormant",
        }.get(metric, metric)
        if n == 0:
            return "Tidak ada data cabang ditemukan."
        # Top 5 summary untuk teks
        top5 = features[:5]
        lines = [f"Peta sebaran {n} cabang Bank Jatim berdasarkan **{metric_label}**:\n"]
        for i, f in enumerate(top5, 1):
            val = f.get(metric if metric != "total" else "total", 0)
            val_str = f"{val:,.0f}" if metric != "pct_dormant" else f"{val:.1f}%"
            lines.append(f"{i}. {f['cabang_name']} ({f['kota']}) — {metric_label}: {val_str}")
        if n > 5:
            lines.append(f"\n...dan {n - 5} cabang lainnya ditampilkan di peta.")
        lines.append("\nKlik marker di peta untuk melihat detail per cabang.")
        return "\n".join(lines)

    rows = result.get("rows", [])
    if not rows:
        return "Tidak ada data ditemukan untuk pertanyaan ini."

    cols = list(rows[0].keys())

    # Build tabel plain text
    col_widths = {c: max(len(c), max(len(str(r.get(c, ""))) for r in rows)) for c in cols}
    header = "  ".join(c.upper().ljust(col_widths[c]) for c in cols)
    separator = "  ".join("-" * col_widths[c] for c in cols)
    data_lines = [
        "  ".join(str(r.get(c, "")).ljust(col_widths[c]) for c in cols)
        for r in rows
    ]

    table = "\n".join([header, separator] + data_lines)
    row_count = result.get("row_count", len(rows))
    return f"{table}\n\n({row_count} baris data)"
