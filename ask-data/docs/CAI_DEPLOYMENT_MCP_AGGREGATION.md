# CAI Deployment Guide — MCP Server Aggregation (APP 5)

> Panduan ini khusus untuk deploy **APP 5: MCP Server Aggregation** — server MCP baru
> untuk tabel `customer_aggregation` (28 kolom segmentasi rekening nasabah).
>
> Pastikan APP 1 (Qwen LLM) dan tabel `customer_aggregation` di Impala sudah siap sebelum mulai.

---

## Overview

| | |
|---|---|
| **Folder** | `ask-data/mcp_server_aggregation/` |
| **Entry Script** | `data-intelligence/ask-data/mcp_server_aggregation/mcp_entry.py` |
| **Tabel Target** | `customer_aggregation` (28 kolom) |
| **Tools** | `sql_query`, `rekening_summary`, `saldo_analysis`, `status_rekening_distribution` |
| **Port** | Auto-detect dari `CDSW_APP_PORT` |
| **Resource** | 2 vCPU / 4 GiB RAM / No GPU |

---

## Prasyarat

Sebelum deploy APP 5, pastikan:

- [ ] Repo sudah di-clone ke `/home/cdsw/data-intelligence/`
- [ ] Tabel `customer_aggregation` sudah ada di Impala
  - Jalankan DDL di `ask-data/sql/impala_customer_aggregation_ddl.sql`
  - Upload CSV `ask-data/output/customer_aggregation_100.csv` ke S3 terlebih dahulu:
    `s3a://go01-demo/user/cai-demo-se-indonesia/data/customer%20segmentation%20aggregation`
  - Verifikasi: `SELECT COUNT(*) FROM cai_sdx_se_indonesia.customer_aggregation` → 100 rows
- [ ] Credential Impala tersedia (host, user, password)

---

## Step 1: Buat Application Baru di CAI

Menu kiri → **Applications** → **New Application**

---

## Step 2: Isi Form Application

| Field | Nilai |
|---|---|
| **Name** | `<prefix>-ask-data-mcp-aggregation` |
| **Subdomain** | _(auto-fill dari Name)_ |
| **Description** | `MCP Server: customer aggregation analytics tools — Bank Jawa Timur` |
| **Script** | `data-intelligence/ask-data/mcp_server_aggregation/mcp_entry.py` |
| **Engine Kernel** | `Python 3.11` |
| **vCPU** | `2` |
| **Memory** | `4 GiB` |
| **GPU** | Tidak diperlukan |
| **Replicas** | `1` |

Centang: **☑ Enable Unauthenticated Access**

---

## Step 3: Set Environment Variables

### Wajib diisi

| Key | Contoh Nilai | Keterangan |
|---|---|---|
| `IMPALA_HOST` | `coordinator-default-impala-aws.dw-go01-demo-aws.ylcu-atmi.cloudera.site` | Impala coordinator hostname |
| `IMPALA_PORT` | `443` | Port HTTPS (on-prem Knox: `28000`, direct: `21050`) |
| `IMPALA_HTTP_PATH` | `cliservice` | |
| `CDP_USER` | `<cdp-username>` | Username CDP |
| `CDP_PASS` | `<cdp-password>` | Password CDP |
| `DB_NAME` | `cai_sdx_se_indonesia` | Nama database Impala — **sesuaikan** |

### Opsional

| Key | Default | Keterangan |
|---|---|---|
| `TABLE_NAME` | `customer_aggregation` | Override nama tabel jika berbeda di env lain |

> **Tidak perlu** set: `QWEN_BASE_URL`, `CHROMA_*`, `OLLAMA_*`, `EMBED_MODEL`
> — APP 5 hanya butuh koneksi Impala.

---

## Step 4: Deploy dan Verifikasi

Klik **Create Application**. Tunggu status `Running` (1–2 menit).

Setelah Running, ambil URL application dari dashboard lalu jalankan:

```bash
MCP_AGG_URL="https://<subdomain-app5>.<domain-cai-kamu>"

# 1. Health check
curl $MCP_AGG_URL/health
# Expected: {"status":"ok"}

# 2. List tools
curl $MCP_AGG_URL/tools | python3 -m json.tool
# Expected: 4 tools — sql_query, rekening_summary, saldo_analysis, status_rekening_distribution

# 3. Test sql_query
curl -X POST $MCP_AGG_URL/tools/sql_query \
  -H "Content-Type: application/json" \
  -d '{"sql":"SELECT COUNT(*) AS total FROM customer_aggregation"}'
# Expected: {"tool":"sql_query","result":{"columns":["total"],"rows":[{"total":100}],"row_count":1,...}}

# 4. Test rekening_summary
curl -X POST $MCP_AGG_URL/tools/rekening_summary \
  -H "Content-Type: application/json" \
  -d '{"limit": 5}'
# Expected: {"tool":"rekening_summary","result":{"columns":[...],"rows":[...],"row_count":5}}

# 5. Test status_rekening_distribution
curl -X POST $MCP_AGG_URL/tools/status_rekening_distribution \
  -H "Content-Type: application/json" \
  -d '{}'
# Expected: distribusi Aktif/Dormant/Tutup per jenis rekening
```

---

## Step 5: Register ke Cloudera Agent Studio

Setelah APP 5 status `Running`, daftarkan ke Agent Studio:

1. Buka **Agent Studio** di Cloudera AI
2. Buka workflow atau buat workflow baru
3. Di bagian **MCP Servers**, tambahkan konfigurasi berikut:

```json
{
  "mcpServers": {
    "BJT Customer Aggregation": {
      "command": "uvx",
      "args": ["mcp-proxy", "https://<subdomain-app5>.<domain-cai-kamu>/"],
      "env": {}
    }
  }
}
```

> **Kenapa `mcp-proxy`?**
> Agent Studio hanya support runtime `uvx` (Python) dan `npx` (Node.js).
> `mcp-proxy` menjadi bridge antara Agent Studio dan HTTP FastAPI server kita.

---

## Tools yang Tersedia

### 1. `sql_query`
Generic SELECT query terhadap `customer_aggregation`.

```json
{
  "sql": "SELECT jenis_rekening, COUNT(*) AS total FROM customer_aggregation GROUP BY jenis_rekening"
}
```

### 2. `rekening_summary`
Summary rekening per CIF: total rekening, saldo, status, transaksi terakhir.

```json
{
  "cif": "CIF0000001",
  "jenis_rekening": "Tabungan",
  "limit": 20
}
```

### 3. `saldo_analysis`
Distribusi saldo dan pola transaksi kredit/debit per jenis dan status rekening.

```json
{
  "jenis_rekening": "Giro",
  "status_rekening": 1
}
```
> `status_rekening`: `0` = Aktif, `1` = Dormant, `2` = Tutup

### 4. `status_rekening_distribution`
Distribusi status rekening (Aktif/Dormant/Tutup) per jenis rekening dan cabang.

```json
{
  "jenis_rekening": "Tabungan",
  "cabang": "BC001"
}
```

---

## Troubleshooting

### App tidak mau `Running`

Cek logs di CAI Application → **Logs**. Kemungkinan penyebab:
- `ModuleNotFoundError: impyla` → dependencies belum terinstall, restart application
- `mcp_server_aggregation/app/main.py not found` → path script salah, pastikan prefix `data-intelligence/`

### `/health` OK tapi query error

```bash
curl -X POST $MCP_AGG_URL/tools/sql_query \
  -H "Content-Type: application/json" \
  -d '{"sql":"SELECT 1"}'
# Jika error: cek IMPALA_HOST, CDP_USER, CDP_PASS di env vars
```

- `TSocket read 0 bytes` → credential salah atau network tidak bisa reach Impala
- `Table not found` → `DB_NAME` atau `TABLE_NAME` salah, atau tabel belum dibuat di Impala

### Test koneksi Impala dari Workbench session

```bash
cd /home/cdsw/data-intelligence/ask-data

IMPALA_HOST=<host> CDP_USER=<user> CDP_PASS=<pass> \
  python3 scripts/test_impala_connection.py
```

---

## Checklist Final

- [ ] APP 5 status: **Running**
- [ ] `GET /health` → `{"status":"ok"}`
- [ ] `GET /tools` → 4 tools terdaftar
- [ ] `POST /tools/sql_query` dengan `SELECT COUNT(*) AS total FROM customer_aggregation` → `total: 100`
- [ ] `POST /tools/rekening_summary` → data muncul
- [ ] `POST /tools/saldo_analysis` → distribusi saldo muncul
- [ ] `POST /tools/status_rekening_distribution` → distribusi Aktif/Dormant/Tutup muncul
- [ ] Registered di Agent Studio via `mcp-proxy`
