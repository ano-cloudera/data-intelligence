# CAI Deployment Guide — MCP Server: Customer Segments (APP 5)

> Panduan deploy **APP 5: MCP Server Customer Segments** — server MCP untuk tabel
> `customer_segments_staging` (37 kolom, 219.262 baris data segmentasi nasabah Bank Jawa Timur).

---

## Overview

| | |
|---|---|
| **Folder** | `ask-data/mcp_server_aggregation/` |
| **Entry Script** | `data-intelligence/ask-data/mcp_server_aggregation/mcp_entry.py` |
| **Tabel Target** | `customer_segments_staging` (37 kolom) |
| **Tools** | 8 tools: `quick_stats`, `get_schema`, `cabang_performance`, `transaksi_trend`, `status_rekening_distribution`, `saldo_analysis`, `rekening_summary`, `sql_query` |
| **Port** | Auto-detect dari `CDSW_APP_PORT` |
| **Resource** | 2 vCPU / 4 GiB RAM / No GPU |

---

## Konteks Bisnis

Data `customer_segments_staging` adalah hasil enrichment ML segmentasi nasabah Bank Jawa Timur:

- **219.262 rekening** dari seluruh cabang
- **Cluster K-Means** (3 segmen): Silent Mature, Young Syariah Digital, Konvensional Produktif
- **RFM Scoring**: Champions, Loyal, Potential, At Risk, Lost
- **Demografis**: umur, jenis kelamin, age group
- **Aktivitas**: hari sejak transaksi terakhir, activity level (Sangat Aktif / Aktif / Kurang Aktif / Tidak Aktif)
- **Saldo Segment**: Rendah (<1jt) / Menengah (1-10jt) / Tinggi (10-100jt) / Premium (>100jt)

---

## Prasyarat

- [ ] Repo sudah di-clone ke `/home/cdsw/data-intelligence/`
- [ ] File parquet sudah diupload ke S3:
  `s3a://go01-demo/user/cai-demo-se-indonesia/data/customer_segments/customer_segments.parquet`
- [ ] DDL sudah dijalankan di Hue: `ask-data/sql/impala_customer_segments_ddl.sql`
- [ ] Verifikasi: `SELECT COUNT(*) FROM cai_sdx_se_indonesia.customer_segments_staging` → 219.262 rows

---

## Step 1: Buat Application Baru di CAI

Menu kiri → **Applications** → **New Application**

---

## Step 2: Isi Form Application

| Field | Nilai |
|---|---|
| **Name** | `<prefix>-ask-data-mcp-aggregation` |
| **Description** | `MCP Server: customer segments analytics — Bank Jawa Timur` |
| **Script** | `data-intelligence/ask-data/mcp_server_aggregation/mcp_entry.py` |
| **Engine Kernel** | `Python 3.11` |
| **vCPU** | `2` |
| **Memory** | `4 GiB` |
| **GPU** | Tidak diperlukan |

Centang: **☑ Enable Unauthenticated Access**

---

## Step 3: Set Environment Variables

| Key | Nilai | Keterangan |
|---|---|---|
| `IMPALA_HOST` | `coordinator-default-impala-aws.dw-go01-demo-aws.ylcu-atmi.cloudera.site` | Impala coordinator |
| `IMPALA_PORT` | `443` | Port HTTPS |
| `IMPALA_HTTP_PATH` | `cliservice` | |
| `CDP_USER` | `<cdp-username>` | |
| `CDP_PASS` | `<cdp-password>` | |
| `DB_NAME` | `cai_sdx_se_indonesia` | |
| `TABLE_NAME` | `customer_segments_staging` | **Wajib diisi** |

---

## Step 4: Deploy dan Verifikasi

```bash
MCP_URL="https://<subdomain-app5>.<domain-cai>"

# Health check
curl $MCP_URL/health
# Expected: {"status":"ok","version":"3.0.0","tools":8}

# List tools
curl $MCP_URL/tools

# Test quick_stats
curl $MCP_URL/tools/get_schema

# Test saldo_analysis
curl -X POST $MCP_URL/tools/saldo_analysis \
  -H "Content-Type: application/json" \
  -d '{"status_rekening": 0}'

# Test rekening_summary
curl -X POST $MCP_URL/tools/rekening_summary \
  -H "Content-Type: application/json" \
  -d '{"limit": 5}'
```

---

## Step 5: Register ke Agent Studio

```json
{
  "mcpServers": {
    "BJT Customer Aggregation": {
      "command": "uvx",
      "args": ["mcp-proxy", "https://<subdomain-app5>.<domain-cai>/"],
      "env": {}
    }
  }
}
```

---

## System Prompt — Data Retrieval Agent

```
Kamu adalah Data Retrieval Agent untuk workflow analitik segmentasi nasabah Bank Jawa Timur.

Tugas kamu adalah memahami kebutuhan data, memilih MCP tool yang paling tepat, menjalankan pengambilan data, dan mengembalikan hasil secara faktual ke Master Agent.

Data berasal dari tabel customer_segments_staging yang berisi 219.262 rekening nasabah hasil segmentasi ML dengan 37 kolom mencakup: identitas rekening, saldo, aktivitas transaksi, demografis nasabah, cluster segmentasi, dan RFM scoring.

KONTEKS BISNIS:
- Cluster 0 (Silent Mature): nasabah dengan transaksi sangat jarang, saldo rendah, berisiko churn
- Cluster 1 (Young Syariah Digital): nasabah muda berbasis Syariah, aktivitas tinggi, orientasi digital
- Cluster 2 (Konvensional Produktif): nasabah konvensional aktif, saldo tertinggi, transaksi terbanyak
- RFM Champions/Loyal: nasabah bernilai tinggi, prioritas retensi
- RFM At Risk/Lost: nasabah yang perlu reaktivasi segera
- activity_level: Sangat Aktif (<=7hr), Aktif (8-30hr), Kurang Aktif (31-180hr), Tidak Aktif (>180hr)
- status_rekening: 0=Aktif, 1=Dormant, 2=Tutup (integer, tidak perlu CAST)

ATURAN WAJIB — JANGAN LOOPING:
1. Maksimal 2 tool call per pertanyaan. Setelah 2 call, LANGSUNG kembalikan hasil.
2. Setelah tool berhasil return data, JANGAN "Thinking" lagi. Kembalikan data apa adanya SEKARANG.
3. Jika satu tool sudah cukup menjawab, jangan panggil tool kedua.
4. Jangan format ulang, ringkas, atau analisis data — itu tugas Master Agent.

PRIORITAS TOOL (pilih SATU yang paling sesuai):
- quick_stats → overview umum, statistik rekening, cluster summary, RFM summary
- cabang_performance → performa cabang, ranking cabang, tidak aktif per cabang
- saldo_analysis → avg saldo, jumlah rekening per status/jenis, aktivitas
- transaksi_trend → tren aktivitas per jenis rekening, hari sejak transaksi
- status_rekening_distribution → distribusi Aktif/Dormant/Tutup per jenis dan cabang
- rekening_summary → daftar rekening per cluster/RFM/segmen, top N rekening
- get_schema → HANYA sebelum sql_query
- sql_query → HANYA jika 7 tool di atas tidak cukup

PENTING — kolom numerik sudah native type (DOUBLE/BIGINT/INT), tidak perlu CAST.

Jangan tampilkan CIF atau nomor rekening. Semua hasil harus agregat.
Jangan berikan rekomendasi bisnis. Fokus pada angka dan fakta.
Jawab dalam Bahasa Indonesia.
```

---

## Contoh Pertanyaan untuk Demo

### Overview & Segmentasi

- Berikan ringkasan data nasabah Bank Jawa Timur
- Berapa jumlah nasabah per cluster segmentasi?
- Tampilkan distribusi RFM segment nasabah kita
- Nasabah dengan kategori Champions ada berapa dan berapa rata-rata saldonya?
- Bandingkan rata-rata saldo antara cluster Silent Mature, Young Syariah Digital, dan Konvensional Produktif

### Aktivitas & Dormant

- Berapa persen rekening yang tidak aktif lebih dari 180 hari per jenis rekening?
- Tampilkan rekening dengan activity level Tidak Aktif per cabang
- Cabang mana yang memiliki persentase rekening dormant tertinggi? Tampilkan top 3
- Berapa rekening yang sudah lebih dari 6 bulan tidak bertransaksi?

### Saldo & Segmen

- Apa rata-rata saldo nasabah Champions vs At Risk?
- Tampilkan distribusi saldo segment (Rendah/Menengah/Tinggi/Premium) per status rekening
- Berapa total rekening dengan saldo Premium yang masih aktif?
- Bandingkan rata-rata saldo antara rekening Syariah dan Konvensional

### Demografis

- Bagaimana distribusi nasabah berdasarkan kelompok usia (age group)?
- Berapa rekening yang dimiliki nasabah muda (<30 tahun) dan berapa rata-rata saldonya?
- Tampilkan perbandingan aktivitas antara nasabah pria dan wanita

### Cabang & Produk

- Tampilkan performa top 5 cabang berdasarkan rata-rata saldo
- Cabang mana yang paling banyak memiliki nasabah kategori Lost?
- Berapa rekening per jenis rekening yang masuk cluster Young Syariah Digital?

---

## Tools yang Tersedia

### 1. `quick_stats`

Overview 4 dimensi sekaligus: status rekening, cluster, RFM, top cabang.
Tidak perlu parameter.

### 2. `cabang_performance`

Performa semua cabang: aktif/dormant/tutup, pct dormant, avg saldo, avg hari sejak transaksi.
Tidak perlu parameter.

### 3. `saldo_analysis`

```json
{"jenis_rekening": "TABUNGAN IB BAROKAH", "status_rekening": 0}
```

### 4. `transaksi_trend`

```json
{"jenis_rekening": "TABUNGAN SIMPEDA"}
```

### 5. `status_rekening_distribution`

```json
{"cabang": "611"}
```

### 6. `rekening_summary`

```json
{"status_rekening": 1, "limit": 10}
```

### 7. `sql_query`

```json
{
  "sql": "SELECT cluster_label, rfm_segment, COUNT(*) AS total, ROUND(AVG(saldo_t0),0) AS avg_saldo FROM cai_sdx_se_indonesia.customer_segments_staging GROUP BY cluster_label, rfm_segment ORDER BY avg_saldo DESC"
}
```

---

## Checklist Final

- [ ] APP 5 status: **Running**
- [ ] `GET /health` → `{"status":"ok","tools":8}`
- [ ] `GET /tools` → 8 tools terdaftar
- [ ] `TABLE_NAME=customer_segments_staging` di env
- [ ] `SELECT COUNT(*) FROM customer_segments_staging` → 219.262 rows
- [ ] Registered di Agent Studio via `mcp-proxy`
