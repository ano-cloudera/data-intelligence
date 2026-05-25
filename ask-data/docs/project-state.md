# Ask Data — Project State (Bank Jawa Timur PoC)

_Last updated: 2026-05-23_

---

## 1. Executive Summary

**Customer:** Bank Jawa Timur (Bank Jatim)
**Use Case:** AI-powered Customer Segmentation Analytics Assistant — Multi-Agent + MCP + Impala CDW
**Status:** ✅ End-to-end working di CAI, siap demo

Asisten analitik berbahasa Indonesia yang memungkinkan tim bisnis mengajukan pertanyaan tentang data segmentasi nasabah dalam bahasa alami. Arsitektur multi-agent (Master → Retrieval → Penasihat) dengan MCP Server yang terhubung ke Impala CDW. Agent Retrieval mengambil data via MCP tools, Agent Penasihat memberikan insight dan rekomendasi bisnis.

---

## 2. Architecture

| Layer | Teknologi |
|---|---|
| Structured data | Impala CDW (Cloudera Data Warehouse) |
| LLM provider | Qwen2.5-14B-Instruct-AWQ via vLLM (CAI Application) |
| MCP Server | FastAPI + MCP Python SDK (SSE transport) |
| Agent orchestration | Cloudera Agent Studio (multi-agent workflow) |
| Data storage | S3 → Parquet → Impala External Table |

### CAI Applications (4 apps)

| App | Nama | Fungsi |
|---|---|---|
| APP 1 | Qwen vLLM | LLM inference engine (GPU) |
| APP 2 | Ask-the-Data Backend | FastAPI backend NL→SQL |
| APP 3 | Ask-the-Data Frontend | Next.js UI |
| APP 5 | MCP Server Aggregation | MCP tools untuk customer_segments_staging |

---

## 3. Data Model

**Database:** `cai_sdx_se_indonesia`
**Table:** `customer_segments_staging`
**Rows:** 1.000 (sample dari 219.262 rows, stratified by cluster)
**Storage:** S3 Parquet → `s3a://go01-demo/user/cai-demo-se-indonesia/data/customer_segments/`
**Format:** PARQUET (External Table)

### Kolom utama (37 kolom)

| Kolom | Tipe | Keterangan |
|---|---|---|
| cif | STRING | ID nasabah (tidak ditampilkan) |
| no_rekening | STRING | Nomor rekening (tidak ditampilkan) |
| jenis | STRING | KONVEN / SYARIAH |
| jenis_rekening | STRING | TABUNGAN SIMPEDA, TABUNGAN IB BAROKAH, dll |
| cabang | STRING | Kode cabang |
| saldo_t0 | DOUBLE | Saldo saat ini |
| total_tx | BIGINT | Total transaksi |
| status_rekening | TINYINT | 0=Aktif, 1=Dormant, 2=Tutup |
| status_label | STRING | Aktif / Dormant / Tutup |
| umur | INT | Usia nasabah |
| hari_sejak_trx | BIGINT | Hari sejak transaksi terakhir |
| cluster_label | STRING | Silent Mature / Young Syariah Digital / Konvensional Produktif |
| rfm_segment | STRING | Champions / Loyal / Potential / At Risk / Lost |
| rfm_score | BIGINT | Total RFM score |
| activity_level | STRING | Sangat Aktif / Aktif / Kurang Aktif / Tidak Aktif |
| saldo_segment | STRING | Rendah / Menengah / Tinggi / Premium |
| age_group | STRING | Kelompok usia |

### Distribusi Data Sample

| Status | Jumlah | % |
|---|---|---|
| Aktif | 700 | 70% |
| Dormant | 200 | 20% |
| Tutup | 100 | 10% |

| Cluster | Jumlah |
|---|---|
| Konvensional Produktif | ~669 |
| Silent Mature | ~183 |
| Young Syariah Digital | ~148 |

---

## 4. MCP Server (APP 5)

**Folder:** `ask-data/mcp_server_aggregation/`
**Entry:** `mcp_server_aggregation/mcp_entry.py`
**Port:** Auto-detect dari `CDSW_APP_PORT`
**Tools:** 8 tools

### Tools yang tersedia

| Tool | Fungsi |
|---|---|
| `quick_stats` | Overview 4 dimensi: status, cluster, RFM, top cabang (4 query paralel) |
| `get_schema` | Daftar kolom dan tipe data |
| `cabang_performance` | Performa semua cabang: aktif/dormant/tutup, avg saldo, LIMIT 50 |
| `transaksi_trend` | Tren aktivitas per jenis rekening |
| `status_rekening_distribution` | Distribusi status per jenis dan cabang, LIMIT 30 |
| `saldo_analysis` | Avg/min/max saldo per jenis/status |
| `rekening_summary` | Ringkasan per cluster/RFM/segmen, default 20 max 100 |
| `sql_query` | Free SELECT query (last resort) |

### Fitur teknis MCP Server

- **Connection pool:** 5 koneksi Impala, reused across calls
- **Parallel queries:** `quick_stats` jalankan 4 query serentak via ThreadPoolExecutor
- **Query timeout:** `QUERY_TIMEOUT_S=30` — query >30 detik di-kill otomatis
- **Stop signal:** Setiap response diakhiri signal `FINAL_ANSWER` untuk cegah Qwen ReAct looping
- **Output format:** Plain text ljust alignment (bukan markdown — Agent Studio tidak render markdown)

### Environment Variables APP 5

| Key | Nilai |
|---|---|
| `IMPALA_HOST` | `coordinator-default-impala-aws.dw-go01-demo-aws.ylcu-atmi.cloudera.site` |
| `IMPALA_PORT` | `443` |
| `IMPALA_HTTP_PATH` | `cliservice` |
| `CDP_USER` | `<cdp-username>` |
| `CDP_PASS` | `<cdp-password>` |
| `DB_NAME` | `cai_sdx_se_indonesia` |
| `TABLE_NAME` | `customer_segments_staging` |

---

## 5. Agent Studio — Multi-Agent Workflow

### Agents

| Agent | Role | Tools |
|---|---|---|
| Master Agent | Orchestrator — routing pertanyaan ke sub-agent | Tidak ada |
| Data Retrieval Agent | Ambil data dari Impala via MCP | BJT Customer Aggregation MCP |
| Agent Penasihat | Insight bisnis dari data yang sudah diambil | Tidak ada |

### MCP Server Config (Agent Studio)

```json
{
  "mcpServers": {
    "BJT Customer Aggregation": {
      "command": "uvx",
      "args": ["mcp-proxy", "https://<subdomain-app5>.<domain-cai>/sse"],
      "env": {}
    }
  }
}
```

### Anti-looping measures

1. Retrieval Agent: max 2 tool call per pertanyaan, STOP setelah tool return
2. MCP response: stop signal `FINAL_ANSWER` di setiap output tool
3. Penasihat Agent: tidak punya tools, output format dibatasi 2-3 insight + 3-5 rekomendasi

---

## 6. Data Generation

**Script:** `ask-data/data_generation/generate_customer_segments_sample.py`
**Input:** `customer_segments.parquet` (219.262 rows)
**Output:** `customer_segments_sample_1k.parquet` (1.000 rows)

### Yang dilakukan script

1. Stratified sample 1.000 rows by `cluster_label` (preserve proporsi)
2. Simulasi `status_rekening`: 70% Aktif, 20% Dormant, 10% Tutup
3. Update kolom turunan: `status_label`, `hari_sejak_trx`, `activity_level`, `rfm_r`, `rfm_score`, `rfm_segment`
4. Write via pyarrow explicit schema — semua string → `pa.string()` (bukan `large_string`)

### Upload ke Impala

```bash
# Upload parquet ke S3
s3a://go01-demo/user/cai-demo-se-indonesia/data/customer_segments/

# Di Hue:
REFRESH cai_sdx_se_indonesia.customer_segments_staging;
COMPUTE STATS cai_sdx_se_indonesia.customer_segments_staging;
# Expected: Updated 1 partition(s) and 37 column(s)
# #Rows: 1000, Format: PARQUET
```

---

## 7. DDL

File: `ask-data/sql/impala_customer_segments_ddl.sql`

```sql
CREATE EXTERNAL TABLE IF NOT EXISTS cai_sdx_se_indonesia.customer_segments_staging (
    cif STRING, no_rekening STRING, jenis STRING, jenis_rekening STRING,
    cabang STRING, saldo_t0 DOUBLE, total_tx BIGINT, status_rekening TINYINT,
    status_label STRING, t0 STRING, umur INT, jenis_kelamin STRING,
    hari_sejak_trx BIGINT, rasio_kredit DOUBLE,
    cluster_kmeans BIGINT, cluster_gmm BIGINT,
    gmm_max_prob DOUBLE, gmm_entropy DOUBLE,
    gmm_p0 DOUBLE, gmm_p1 DOUBLE, gmm_p2 DOUBLE, gmm_p3 DOUBLE,
    gmm_p4 DOUBLE, gmm_p5 DOUBLE, gmm_p6 DOUBLE, gmm_p7 DOUBLE,
    cluster_label STRING, cluster_color STRING, age_group STRING,
    jenis_kelamin_label STRING, saldo_segment STRING, activity_level STRING,
    rfm_r BIGINT, rfm_f BIGINT, rfm_m BIGINT, rfm_score BIGINT, rfm_segment STRING
)
STORED AS PARQUET
LOCATION 's3a://go01-demo/user/cai-demo-se-indonesia/data/customer_segments/';
```

**Catatan:** `t0` pakai STRING bukan TIMESTAMP, `status_rekening` TINYINT (int8)

---

## 8. Progress Checklist

### ✅ Selesai

#### Data & Infrastructure
- [x] Table `customer_segments_staging` — 37 kolom, 1.000 rows sample di Impala CDW
- [x] DDL Impala External Table PARQUET
- [x] COMPUTE STATS dijalankan — #Rows: 1000, 37 columns
- [x] Parquet schema fix: `large_string` → `pa.string()`, `cluster_label` preserved
- [x] Distribusi status simulasi: 70% Aktif, 20% Dormant, 10% Tutup

#### MCP Server (APP 5)
- [x] 8 MCP tools untuk `customer_segments_staging`
- [x] Connection pool 5 koneksi Impala
- [x] Parallel query execution (`quick_stats` 4 query serentak)
- [x] Query timeout 30 detik
- [x] Stop signal `FINAL_ANSWER` di setiap tool response
- [x] Plain text output format (bukan markdown)
- [x] LIMIT di semua tools (cabang_performance LIMIT 50, dll)
- [x] APP 5 running di CAI

#### Agent Studio
- [x] Multi-agent workflow: Master → Retrieval → Penasihat
- [x] MCP terdaftar di Retrieval Agent
- [x] System prompt Retrieval diupdate ke `customer_segments_staging`
- [x] Anti-looping rules di semua agent prompt

### 🔄 Sedang Di-test

- [ ] Verifikasi stop signal efektif cegah Qwen ReAct looping
- [ ] End-to-end test 10 pertanyaan demo

### ❌ Belum / Next Steps

- [ ] Tambah data lebih besar (saat ini 1.000 rows — bisa naik ke 10.000 jika perlu)
- [ ] Migrate MCP ke FastMCP (lebih ringkas, less boilerplate)
- [ ] RAG integration untuk dokumen kebijakan Bank Jatim

---

## 9. Contoh Pertanyaan Demo

1. `Berikan ringkasan performa nasabah Bank Jawa Timur berdasarkan cluster segmentasi`
2. `Cabang mana yang paling banyak rekening dormant dan berapa rata-rata saldonya?`
3. `Berapa rata-rata saldo nasabah Champions?`
4. `Berapa rekening yang tidak aktif lebih dari 180 hari per jenis rekening?`
5. `Tampilkan distribusi saldo segment per status rekening`
6. `Bandingkan jumlah rekening antara nasabah pria dan wanita per cluster`
7. `Berapa jumlah nasabah per cluster segmentasi dan rata-rata saldonya?`
8. `Tampilkan performa semua cabang berdasarkan jumlah rekening aktif dan rata-rata saldo`
9. `Bagaimana distribusi nasabah berdasarkan kelompok usia?`
10. `Bandingkan rata-rata hari sejak transaksi antara rekening Aktif, Dormant, dan Tutup`

---

## 10. Resume Instructions

Saat mulai session baru, assume:
1. Use case: Customer Segmentation Analytics, Bank Jawa Timur
2. Data: `cai_sdx_se_indonesia.customer_segments_staging`, 1.000 rows di Impala CDW
3. LLM: Qwen2.5-14B-Instruct-AWQ via vLLM di CAI (APP 1)
4. MCP Server: APP 5 di CAI — 8 tools untuk `customer_segments_staging`
5. Agent Studio: multi-agent workflow (Master → Retrieval → Penasihat)
6. Semua flow sudah deployed di CAI — fokus ke testing dan demo polish
7. Repo: `https://github.com/ano-cloudera/data-intelligence`
8. MCP folder: `ask-data/mcp_server_aggregation/`

---

End of project state.
