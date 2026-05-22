from __future__ import annotations

from app.impala_client import qualified_table, table_name

COLUMNS = [
    ("cif",                 "STRING",  "Customer Identification"),
    ("no_rekening",         "STRING",  "Nomor rekening"),
    ("jenis",               "STRING",  "Jenis nasabah: Perorangan / Badan Usaha"),
    ("name",                "STRING",  "Nama nasabah"),
    ("cabang",              "STRING",  "Kode cabang: BC001–BC010"),
    ("jenis_rekening",      "STRING",  "Tabungan / Giro / Deposito"),
    ("name_cabang",         "STRING",  "Nama cabang"),
    ("min_saldo",           "STRING",  "Saldo minimum periode — CAST AS DECIMAL(20,2)"),
    ("saldo_t0",            "STRING",  "Saldo pada periode t0 — CAST AS DECIMAL(20,2)"),
    ("tgl_trx_terakhir",    "STRING",  "Tanggal transaksi terakhir (YYYY-MM-DD)"),
    ("total_tx",            "STRING",  "Total transaksi — CAST AS INT"),
    ("tx_sistem",           "STRING",  "Transaksi sistem/auto — CAST AS INT"),
    ("tx_nasabah",          "STRING",  "Transaksi nasabah — CAST AS INT"),
    ("count_tx_kredit",     "STRING",  "Jumlah transaksi kredit — CAST AS INT"),
    ("avg_nominal_kredit",  "STRING",  "Rata-rata nominal kredit — CAST AS DECIMAL(20,2)"),
    ("max_nominal_kredit",  "STRING",  "Nominal kredit tertinggi — CAST AS DECIMAL(20,2)"),
    ("min_nominal_kredit",  "STRING",  "Nominal kredit terendah — CAST AS DECIMAL(20,2)"),
    ("std_nominal_kredit",  "STRING",  "Std dev nominal kredit — CAST AS DECIMAL(20,2)"),
    ("count_tx_debit",      "STRING",  "Jumlah transaksi debit — CAST AS INT"),
    ("avg_nominal_debit",   "STRING",  "Rata-rata nominal debit — CAST AS DECIMAL(20,2)"),
    ("max_nominal_debit",   "STRING",  "Nominal debit tertinggi — CAST AS DECIMAL(20,2)"),
    ("min_nominal_debit",   "STRING",  "Nominal debit terendah — CAST AS DECIMAL(20,2)"),
    ("std_nominal_debit",   "STRING",  "Std dev nominal debit — CAST AS DECIMAL(20,2)"),
    ("has_tx_first_6m",     "STRING",  "Ada transaksi 6 bulan pertama: 'TRUE'/'FALSE'"),
    ("has_tx_last_6m",      "STRING",  "Ada transaksi 6 bulan terakhir: 'TRUE'/'FALSE'"),
    ("saldo_end_target",    "STRING",  "Target saldo akhir — CAST AS DECIMAL(20,2)"),
    ("status_rekening",     "STRING",  "Status: '0'=Aktif, '1'=Dormant, '2'=Tutup"),
    ("t0",                  "STRING",  "Reference date periode (YYYY-MM-DD)"),
]


def run_get_schema() -> dict:
    lines = [
        f"Tabel: {qualified_table()}",
        f"Nama pendek: {table_name()}",
        "",
        "PENTING — semua kolom bertipe STRING di staging table:",
        "- Kolom numerik: wajib CAST(kolom AS DECIMAL(20,2)) atau CAST(kolom AS INT)",
        "- Kolom boolean: gunakan UPPER(kolom) = 'TRUE' atau = 'FALSE'",
        "- Kolom status_rekening: '0'=Aktif, '1'=Dormant, '2'=Tutup",
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
