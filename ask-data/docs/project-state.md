# Ask Data — Project State (Bank Jawa Timur PoC)

_Last updated: 2026-06-08_

---

## 1. Executive Summary

**Customer:** Bank Jawa Timur (Bank Jatim)
**Use Case:** AI-powered Customer Segmentation Analytics Assistant — Multi-Agent + MCP + Impala CDW
**Status:** ✅ End-to-end working di CAI, siap demo

Asisten analitik berbahasa Indonesia yang memungkinkan tim bisnis mengajukan pertanyaan tentang data segmentasi nasabah dalam bahasa alami. Arsitektur multi-agent (Master → Greeting → Retrieval) dengan MCP Server yang terhubung ke Impala CDW.

---

## 2. Architecture

| Layer | Teknologi |
|---|---|
| Structured data | Impala CDW (Cloudera Data Warehouse) |
| LLM provider | Qwen2.5-14B-Instruct-AWQ via vLLM (CAI Application) |
| MCP Server | FastAPI + MCP Python SDK (SSE transport) |
| Agent orchestration | Cloudera Agent Studio (multi-agent workflow) |
| Data storage | S3 → Parquet → Impala External Table |

### CAI Applications

| App | Nama di CAI | Fungsi |
|---|---|---|
| APP 1 | `bjt-qwen` | LLM inference engine (GPU, Qwen2.5-14B-AWQ) |
| APP 2 | `bjt-ask-data-backend` | FastAPI backend NL→SQL + aggregation proxy |
| APP 3 | `bjt-ask-data-frontend` | Next.js UI |
| APP 4 | `bjt-ask-data-mcp` | MCP server lama (customer_dormant_segment) — legacy |
| APP 5 | `bjt-mcp-aggregation` | MCP tools untuk customer_segments_staging (aktif, 10 tools) |
| APP 6 | `bjt-lightmem` | LightMem memory server — persistensi memori antar sesi AI |

### URLs

| App | URL |
|---|---|
| APP 5 MCP | `https://bjt-mcp-aggregation.ml-dbfc64d1-783.go01-dem.ylcu-atmi.cloudera.site` |

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
| jenis_kelamin_label | STRING | Laki-laki / Perempuan |

### Distribusi Data Sample

| Status | Jumlah | % |
|---|---|---|
| Aktif | ~700 | 70% |
| Dormant | ~200 | 20% |
| Tutup | ~100 | 10% |

| Cluster | Jumlah |
|---|---|
| Konvensional Produktif | ~669 |
| Silent Mature | ~183 |
| Young Syariah Digital | ~148 |

---

## 4. MCP Server — APP 5 (`bjt-mcp-aggregation`)

**Folder:** `ask-data/mcp_server_aggregation/`
**Entry:** `data-intelligence/ask-data/mcp_server_aggregation/mcp_entry.py`
**Version:** 3.1.0
**Tools:** 10 tools
**URL:** `https://bjt-mcp-aggregation.ml-dbfc64d1-783.go01-dem.ylcu-atmi.cloudera.site`

### Tools yang tersedia (10 tools)

| Tool | Fungsi | Parameter |
|---|---|---|
| `quick_stats` | Overview 4 dimensi: status, cluster, RFM, top cabang | - |
| `get_schema` | Daftar kolom dan tipe data | - |
| `cabang_performance` | Performa cabang: aktif/dormant/tutup, avg saldo | `order_by`, `limit` |
| `transaksi_trend` | Tren aktivitas per jenis rekening | `jenis_rekening` (opsional) |
| `status_rekening_distribution` | Distribusi status per jenis dan cabang | `jenis_rekening`, `cabang` (opsional) |
| `saldo_analysis` | Avg/min/max saldo per jenis/status | `jenis_rekening`, `status_rekening` (opsional) |
| `rekening_summary` | Ringkasan per cluster/RFM/segmen | `cluster_label`, `rfm_segment`, `limit` |
| `cluster_summary` | Karakteristik cluster: saldo, umur, gender, RFM | `cluster_label` (opsional) |
| `demografis_summary` | Distribusi gender, age group, activity level | - |
| `sql_query` | Free SELECT query (last resort) | `sql` |

### Fitur teknis MCP Server

- **Connection pool:** 5 koneksi Impala, reused across calls
- **Parallel queries:** `quick_stats` jalankan 4 query serentak via ThreadPoolExecutor
- **Query timeout:** `QUERY_TIMEOUT_S=30`
- **Stop signal:** Setiap response diakhiri signal `FINAL_ANSWER`
- **Output format:** Plain text ljust alignment

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

### MCP Config untuk Agent Studio

```json
{
  "mcpServers": {
    "BJT Customer Aggregation": {
      "command": "uvx",
      "args": ["mcp-proxy", "https://bjt-mcp-aggregation.ml-dbfc64d1-783.go01-dem.ylcu-atmi.cloudera.site/sse"],
      "env": {}
    }
  }
}
```

---

## 4b. LightMem Memory Server — APP 6 (`bjt-lightmem`)

**Folder:** `ask-data/lightmem_server/`
**Entry:** `data-intelligence/ask-data/lightmem_server/lightmem_entry.py`
**Framework:** LightMem (ICLR 2026) — PreCompressor → TopicSegmenter → MemoryManager → TextEmbedder → Qdrant
**Status:** Scaffolded lokal, belum deploy ke CAI

### Tools MCP LightMem

| Tool | Fungsi |
|---|---|
| `add_memory` | Simpan teks ke memori jangka panjang |
| `retrieve_memory` | Cari memori relevan berdasarkan query |
| `offline_update` | Trigger proses background memory consolidation |
| `show_memory_status` | Status memori: jumlah item, ukuran store |

### Environment Variables APP 6

| Key | Nilai |
|---|---|
| `QWEN_BASE_URL` | `https://bjt-qwen.ml-dbfc64d1-783.go01-dem.ylcu-atmi.cloudera.site/v1` |
| `QWEN_API_KEY` | `local-dev-token` |
| `QWEN_MODEL` | `Qwen/Qwen2.5-14B-Instruct-AWQ` |
| `MEMORY_STORE_PATH` | `./bjt_memory_store` |

### Requirements APP 6

```text
lightmem @ git+https://github.com/zjunlp/LightMem.git
fastmcp>=2.0.0
sentence-transformers>=2.2.0
qdrant-client>=1.7.0
torch>=2.0.0
```

---

## 5. Agent Studio — Multi-Agent Workflow

### Agents

| Agent | Role | Tools |
|---|---|---|
| Master Agent Segmentasi | Koordinator — greeting + routing ke sub-agent | Tidak ada |
| Greeting Agent | Sambut user di pesan pertama | Tidak ada |
| Data Retrieval Agent | Ambil data dari Impala via MCP | BJT Customer Aggregation MCP |

### Anti-looping measures

1. Master Agent: instruksi tool eksplisit ke Retrieval Agent
2. Retrieval Agent: max 1 tool call, langsung Final Answer
3. MCP response: stop signal `FINAL_ANSWER` di setiap output tool
4. `/no_think` di semua agent prompt

---

## 6. Backend — APP 2 (`bjt-ask-data-backend`)

### Aggregation Proxy Endpoints

| Endpoint | Fungsi |
|---|---|
| `GET /aggregation/health` | Cek koneksi ke APP 5 |
| `GET /aggregation/tools` | List tools APP 5 |
| `POST /aggregation/query` | Call tool APP 5 dari backend |

### Environment Variables APP 2 (tambahan)

| Key | Nilai |
|---|---|
| `MCP_AGGREGATION_URL` | `https://bjt-mcp-aggregation.ml-dbfc64d1-783.go01-dem.ylcu-atmi.cloudera.site` |

---

## 7. Frontend — APP 3 (`bjt-ask-data-frontend`)

**Framework:** Next.js 15 + React 18 + Tailwind CSS

### Fitur Settings Panel

| Fitur | Keterangan |
|---|---|
| Model selector | Dropdown model Qwen yang tersedia |
| Table Lock | Lock query ke tabel spesifik per sesi |
| RAG / Knowledge Base | Auto-routing aktif jika ChromaDB tersedia |
| MCP Servers | Dynamic list: add/remove/test multiple MCP servers |

### MCP Servers Config (localStorage)

User bisa tambah banyak MCP server langsung dari UI Settings tanpa env var. Disimpan di browser `localStorage` key `mcp_servers` sebagai array JSON:

```json
[
  {
    "id": "uuid-v4",
    "name": "MCP Aggregation",
    "url": "https://bjt-mcp-aggregation.ml-dbfc64d1-783.go01-dem.ylcu-atmi.cloudera.site",
    "status": "connected"
  }
]
```

Tiap entry bisa di-**Test** (dot hijau/merah) dan di-**Delete** dari UI.

---

## 7. Data Generation

**Script:** `ask-data/data_generation/generate_customer_segments_sample.py`
**Input:** `customer_segments.parquet` (219.262 rows)
**Output:** `customer_segments_sample_1k.parquet` (1.000 rows)

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

## 8. DDL

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

---

## 9. Progress Checklist

### ✅ Selesai

#### Data & Infrastructure
- [x] Table `customer_segments_staging` — 37 kolom, 1.000 rows sample di Impala CDW
- [x] COMPUTE STATS dijalankan — #Rows: 1000, 37 columns
- [x] Distribusi status: 70% Aktif, 20% Dormant, 10% Tutup

#### MCP Server (APP 5 — `bjt-mcp-aggregation`)
- [x] 10 MCP tools untuk `customer_segments_staging`
- [x] Connection pool 5 koneksi Impala
- [x] Query timeout 30 detik
- [x] Stop signal `FINAL_ANSWER` di setiap tool response
- [x] `cluster_summary` dengan filter `cluster_label` dan kolom gender (Laki-laki/Perempuan)
- [x] `demografis_summary` untuk distribusi gender, usia, activity level
- [x] REST endpoint `GET /tools/quick_stats`, `GET /tools/cluster_summary`, `GET /tools/demografis_summary`
- [x] Allow Unauthenticated Access aktif
- [x] APP 5 running di CAI

#### Agent Studio
- [x] Multi-agent workflow: Master → Greeting → Retrieval
- [x] Greeting Agent — sapaan awal tanpa MCP
- [x] MCP terdaftar di Retrieval Agent saja
- [x] Anti-looping rules di semua agent prompt

#### Backend (APP 2)
- [x] Aggregation proxy: `/aggregation/health`, `/aggregation/tools`, `/aggregation/query`
- [x] Auto-routing aggregation: `is_aggregation_request()` + `resolve_aggregation_tool()`
- [x] `MCP_AGGREGATION_URL` env var tersedia

#### Frontend (APP 3)

- [x] MCP Servers config section di Settings panel
- [x] Dynamic list: add/remove/test multiple MCP servers
- [x] Persistent di localStorage key `mcp_servers` sebagai array JSON

#### LightMem (APP 6)

- [x] Scaffold folder `ask-data/lightmem_server/` tersedia di repo
- [x] `server.py` dengan 4 MCP tools: `add_memory`, `retrieve_memory`, `offline_update`, `show_memory_status`
- [x] `config.json` terkonfigurasi untuk Qwen2.5 + CPU embeddings + Qdrant lokal

### 🔄 Pending Deploy ke CAI

- [ ] APP 2: git pull + tambah env `MCP_AGGREGATION_URL` + restart
- [ ] APP 3: git pull + rebuild + restart (untuk MCP Servers UI)
- [ ] APP 5: git pull + restart (gender fix + quick_stats endpoint)
- [ ] APP 6: deploy LightMem ke CAI (belum dibuat sebagai Application)

### ❌ Next Steps

- [ ] Deploy APP 6 (LightMem) ke CAI
- [ ] End-to-end test chat dengan aggregation routing aktif
- [ ] Tambah data lebih besar (saat ini 1.000 rows)

---

## 10. Contoh Pertanyaan Demo

1. `Berikan ringkasan data nasabah Bank Jawa Timur`
2. `Tampilkan top 3 cabang dengan rata-rata saldo tertinggi`
3. `Bagaimana distribusi nasabah berdasarkan kelompok usia?`
4. `Apa karakteristik nasabah cluster Young Syariah Digital?`
5. `Berapa persen nasabah laki-laki vs perempuan?`
6. `Bandingkan ketiga cluster segmentasi nasabah kita`
7. `Berapa rekening dormant dan berapa rata-rata saldonya?`
8. `Tampilkan tren aktivitas transaksi per jenis rekening`

---

## 11. Resume Instructions

Saat mulai session baru, assume:

1. Use case: Customer Segmentation Analytics, Bank Jawa Timur
2. Data: `cai_sdx_se_indonesia.customer_segments_staging`, 1.000 rows di Impala CDW
3. LLM: Qwen2.5-14B-Instruct-AWQ via vLLM — APP 1 (`bjt-qwen`)
4. MCP Server: APP 5 (`bjt-mcp-aggregation`) — 10 tools, URL sudah diketahui
5. Agent Studio: multi-agent workflow (Master → Greeting → Retrieval)
6. Repo: `https://github.com/ano-cloudera/data-intelligence`
7. MCP folder: `ask-data/mcp_server_aggregation/`
8. Frontend: Next.js (APP 3), MCP Servers config via localStorage dynamic array
9. LightMem: scaffolded di `ask-data/lightmem_server/`, belum deploy ke CAI (APP 6)

---

End of project state.
