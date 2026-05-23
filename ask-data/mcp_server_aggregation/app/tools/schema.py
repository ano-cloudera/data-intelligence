from __future__ import annotations

from app.impala_client import qualified_table, table_name

COLUMNS = [
    # Identitas Rekening
    ("cif",                 "STRING",    "Customer Identification"),
    ("no_rekening",         "STRING",    "Nomor rekening"),
    ("jenis",               "STRING",    "Jenis nasabah: SYARIAH / KONVEN"),
    ("jenis_rekening",      "STRING",    "Nama produk rekening, contoh: TABUNGAN IB BAROKAH"),
    ("cabang",              "STRING",    "Kode cabang, contoh: 611"),
    ("status_rekening",     "TINYINT",   "Status: 0=Aktif, 1=Dormant, 2=Tutup — tidak perlu CAST"),
    ("status_label",        "STRING",    "Label status: Aktif / Dormant / Tutup"),
    ("t0",                  "TIMESTAMP", "Reference date periode (YYYY-MM-DD)"),
    # Saldo & Transaksi
    ("saldo_t0",            "DOUBLE",    "Saldo pada periode t0 — tidak perlu CAST"),
    ("total_tx",            "BIGINT",    "Total transaksi — tidak perlu CAST"),
    ("hari_sejak_trx",      "BIGINT",    "Jumlah hari sejak transaksi terakhir — tidak perlu CAST"),
    ("rasio_kredit",        "DOUBLE",    "Rasio transaksi kredit terhadap total — tidak perlu CAST"),
    # Demografis
    ("umur",                "INT",       "Usia nasabah dalam tahun — tidak perlu CAST"),
    ("jenis_kelamin",       "STRING",    "Kode gender: P=Perempuan, L=Laki-laki"),
    ("jenis_kelamin_label", "STRING",    "Label gender: Perempuan / Laki-laki / Tidak Diketahui"),
    ("age_group",           "STRING",    "Kelompok usia: Muda (<30) / Dewasa (30-45) / Matang (45-60) / Senior (>60)"),
    # Segmentasi ML
    ("cluster_kmeans",      "BIGINT",    "Cluster K-Means: 0=Silent Mature, 1=Young Syariah Digital, 2=Konvensional Produktif"),
    ("cluster_label",       "STRING",    "Label cluster: Silent Mature / Young Syariah Digital / Konvensional Produktif"),
    ("cluster_gmm",         "BIGINT",    "Cluster GMM (0-7) — probabilistic clustering"),
    ("gmm_max_prob",        "DOUBLE",    "Probabilitas tertinggi cluster GMM"),
    ("gmm_entropy",         "DOUBLE",    "Entropy distribusi probabilitas GMM"),
    ("gmm_p0",              "DOUBLE",    "Probabilitas cluster GMM 0"),
    ("gmm_p1",              "DOUBLE",    "Probabilitas cluster GMM 1"),
    ("gmm_p2",              "DOUBLE",    "Probabilitas cluster GMM 2"),
    ("gmm_p3",              "DOUBLE",    "Probabilitas cluster GMM 3"),
    ("gmm_p4",              "DOUBLE",    "Probabilitas cluster GMM 4"),
    ("gmm_p5",              "DOUBLE",    "Probabilitas cluster GMM 5"),
    ("gmm_p6",              "DOUBLE",    "Probabilitas cluster GMM 6"),
    ("gmm_p7",              "DOUBLE",    "Probabilitas cluster GMM 7"),
    ("cluster_color",       "STRING",    "Hex color untuk visualisasi cluster"),
    # Label Segmen
    ("saldo_segment",       "STRING",    "Segmen saldo: Rendah (<1jt) / Menengah (1-10jt) / Tinggi (10-100jt) / Premium (>100jt)"),
    ("activity_level",      "STRING",    "Level aktivitas: Sangat Aktif (<=7hr) / Aktif (8-30hr) / Kurang Aktif (31-180hr) / Tidak Aktif (>180hr)"),
    # RFM Scoring
    ("rfm_r",               "BIGINT",    "RFM Recency score 1-5 (5=terbaru)"),
    ("rfm_f",               "BIGINT",    "RFM Frequency score 1-5 (5=paling sering)"),
    ("rfm_m",               "BIGINT",    "RFM Monetary score 1-5 (5=saldo tertinggi)"),
    ("rfm_score",           "BIGINT",    "Total RFM score (3-15)"),
    ("rfm_segment",         "STRING",    "Segmen RFM: Champions / Loyal / Potential / At Risk / Lost"),
]


def run_get_schema() -> dict:
    lines = [
        f"Tabel: {qualified_table()}",
        f"Nama pendek: {table_name()}",
        "",
        "PENTING — tabel ini sudah bertipe native (bukan STRING staging):",
        "- Kolom numerik (DOUBLE, BIGINT, INT, TINYINT): TIDAK perlu CAST",
        "- status_rekening: 0=Aktif, 1=Dormant, 2=Tutup (integer langsung)",
        "- Tidak ada kolom boolean STRING — gunakan hari_sejak_trx untuk cek aktivitas",
        "- Cluster: 0=Silent Mature, 1=Young Syariah Digital, 2=Konvensional Produktif",
        "- RFM segment: Champions / Loyal / Potential / At Risk / Lost",
        "",
        "Kolom tersedia:",
    ]
    for col, dtype, desc in COLUMNS:
        lines.append(f"  {col} ({dtype}) — {desc}")

    return {
        "table": qualified_table(),
        "short_name": table_name(),
        "column_count": len(COLUMNS),
        "schema_info": "\n".join(lines),
    }
