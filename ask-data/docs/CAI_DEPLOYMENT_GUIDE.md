# CAI Deployment Guide — Bank Jawa Timur PoC

Deploy urutan wajib: **APP 1 Qwen LLM → APP 2 Backend → APP 3 MCP Server → APP 4 Frontend**

---

## Persiapan Awal (Lakukan Sekali Sebelum Deploy)

### Step A — Sync Code ke Workbench Session

Di terminal CAI Workbench session, jalankan:

```bash
python sync_project.py
```

Verifikasi folder tersedia:
```bash
ls /home/cdsw/bank-jawa-timur/ask-data/
# Harus ada: backend/ frontend/ mcp_server/ qwen_inference/ docs/ scripts/ sql/
```

---

### Step B — Siapkan ChromaDB (Vector Store)

ChromaDB tidak di-commit ke git, harus disiapkan manual.

**Pilih salah satu cara:**

**Option 1 — Upload dari Mac lokal (lebih cepat, sudah ada 17 chunks):**

Dari terminal Mac lokal:
```bash
# Zip dulu
cd /Users/trianonurhikmat/Documents/Works/cloudera/account/bank-jawa-timur/ask-data
zip -r chroma_db.zip chroma_db/
```
Upload `chroma_db.zip` ke CAI Workbench session via File Upload UI, lalu di terminal session:
```bash
cd /home/cdsw/bank-jawa-timur/ask-data
unzip ~/chroma_db.zip
ls chroma_db/
# Harus ada folder chroma.sqlite3 dan subfolder chunks
```

**Option 2 — Re-ingest PDF di session (jika PDF sudah diupload ke session):**
```bash
cd /home/cdsw/bank-jawa-timur/ask-data
pip install -r backend/requirements.txt -q
PYTHONPATH=backend python scripts/ingest_documents.py
# Expected output: Ingested X chunks into bankjatim_docs
```

Verifikasi ChromaDB:
```bash
python3 -c "
import chromadb
c = chromadb.PersistentClient('/home/cdsw/bank-jawa-timur/ask-data/chroma_db')
col = c.get_collection('bankjatim_docs')
print('Chunks:', col.count())
"
# Expected: Chunks: 17
```

---

## APP 1 — Qwen LLM Application

**Tujuan:** Serve Qwen2.5-14B-Instruct-AWQ via vLLM sebagai OpenAI-compatible inference server.
**Deploy ini PERTAMA** — Backend dan MCP Server butuh URL-nya.

---

### Step 1.1 — Buka halaman Applications

1. Login ke Cloudera AI Workbench
2. Pilih project yang sudah di-sync
3. Di menu kiri, klik **Applications**
4. Klik tombol **New Application**

---

### Step 1.2 — Isi form Application

| Field | Value |
|---|---|
| **Name** | `bank-jatim-qwen-llm` |
| **Subdomain** | `bank-jatim-qwen-llm` _(auto-fill, bisa dibiarkan)_ |
| **Description** | `Qwen2.5-14B-Instruct-AWQ via vLLM — LLM inference server` |
| **Script** | `bank-jawa-timur/ask-data/qwen_inference/qwen_entry.py` |
| **Engine Kernel** | `Python 3.11` |
| **Engine Profile** | Pilih profile GPU dengan **NVIDIA L40** — minimal 1 GPU, 48 GB VRAM |
| **Replicas** | `1` |

Centang: **☑ Enable Unauthenticated Access**

---

### Step 1.3 — Set Environment Variables

Klik tab **Environment Variables**, tambahkan satu per satu:

| Key | Value |
|---|---|
| `QWEN_MODEL` | `Qwen/Qwen2.5-14B-Instruct-AWQ` |
| `QWEN_API_KEY` | `local-dev-token` |
| `QWEN_MAX_MODEL_LEN` | `8192` |
| `QWEN_GPU_MEMORY_UTILIZATION` | `0.90` |
| `QWEN_TENSOR_PARALLEL_SIZE` | `1` |
| `HUGGING_FACE_HUB_TOKEN` | `<isi HF token kamu>` |

> Jika model sudah ter-cache di Workbench, `HUGGING_FACE_HUB_TOKEN` tidak wajib.
> Jika pakai kedua L40 GPU, set `QWEN_TENSOR_PARALLEL_SIZE=2` dan `QWEN_GPU_MEMORY_UTILIZATION=0.85`.

---

### Step 1.4 — Deploy

Klik **Create Application**.

Tunggu status berubah dari `Starting` → `Running`. Bisa memakan waktu **5–15 menit** pertama kali karena download model dari HuggingFace (~8 GB).

Pantau progress di tab **Logs** Application.

---

### Step 1.5 — Catat URL dan Verifikasi

Setelah status `Running`, klik nama Application untuk lihat URL-nya.
Contoh URL: `https://bank-jatim-qwen-llm.ml-xxxxx.cloudera.site`

**Verifikasi dari terminal Workbench session:**
```bash
QWEN_URL="https://bank-jatim-qwen-llm.ml-xxxxx.cloudera.site"

# Test health proxy app
curl $QWEN_URL/health
# Expected: {"status":"ok","provider":"local_qwen",...}

# Test vLLM OpenAI endpoint
curl -X POST $QWEN_URL/v1/chat/completions \
  -H "Authorization: Bearer local-dev-token" \
  -H "Content-Type: application/json" \
  -d '{"model":"Qwen/Qwen2.5-14B-Instruct-AWQ","messages":[{"role":"user","content":"Halo, siapa kamu?"}],"max_tokens":50}'
# Expected: response JSON dengan content jawaban dari Qwen
```

> **Simpan URL ini:** `https://bank-jatim-qwen-llm.ml-xxxxx.cloudera.site`
> Akan dipakai sebagai `QWEN_BASE_URL` di APP 2 dan `OLLAMA_BASE_URL` di APP 2 & 3.

---

## APP 2 — Backend Application

**Tujuan:** FastAPI server — SQL generation, Impala query execution, ChromaDB RAG, session management.
**Deploy setelah APP 1 running.**

---

### Step 2.1 — Buka halaman Applications

1. Di menu kiri, klik **Applications**
2. Klik tombol **New Application**

---

### Step 2.2 — Isi form Application

| Field | Value |
|---|---|
| **Name** | `bank-jatim-backend` |
| **Subdomain** | `bank-jatim-backend` |
| **Description** | `FastAPI backend — NL to SQL, ChromaDB RAG, Impala CDW` |
| **Script** | `bank-jawa-timur/ask-data/backend/backend_entry.py` |
| **Engine Kernel** | `Python 3.11` |
| **Engine Profile** | CPU — **4 vCPU, 8 GB RAM** |
| **Replicas** | `1` |

Centang: **☑ Enable Unauthenticated Access**

---

### Step 2.3 — Set Environment Variables

| Key | Value |
|---|---|
| `LLM_PROVIDER` | `local_qwen` |
| `QWEN_BASE_URL` | `https://bank-jatim-qwen-llm.ml-xxxxx.cloudera.site/v1` |
| `QWEN_API_KEY` | `local-dev-token` |
| `QWEN_MODEL` | `Qwen/Qwen2.5-14B-Instruct-AWQ` |
| `IMPALA_HOST` | `coordinator-default-impala-aws.dw-go01-demo-aws.ylcu-atmi.cloudera.site` |
| `IMPALA_PORT` | `443` |
| `IMPALA_HTTP_PATH` | `cliservice` |
| `CDP_USER` | `triano` |
| `CDP_PASS` | `<cdp-password>` |
| `DB_NAME` | `cai_sdx_se_indonesia` |
| `SESSION_BACKEND` | `sqlite` |
| `SESSION_SQLITE_PATH` | `data/ask_data_sessions.db` |
| `SESSION_TTL_MINUTES` | `60` |
| `MEMORY_MAX_HISTORY` | `10` |
| `GUARDRAILS_ENABLED` | `true` |
| `CHROMA_ENABLED` | `true` |
| `CHROMA_PERSIST_DIR` | `/home/cdsw/bank-jawa-timur/ask-data/chroma_db` |
| `CHROMA_COLLECTION` | `bankjatim_docs` |
| `EMBED_MODEL` | `nomic-embed-text` |
| `OLLAMA_BASE_URL` | `https://bank-jatim-qwen-llm.ml-xxxxx.cloudera.site` |

> **Penting:**
> - `QWEN_BASE_URL` = URL Qwen App + `/v1` di akhir
> - `OLLAMA_BASE_URL` = URL Qwen App **tanpa** `/v1`
> - `CHROMA_PERSIST_DIR` = absolute path, bukan `./chroma_db`

---

### Step 2.4 — Deploy

Klik **Create Application**.

Tunggu status `Running`. Biasanya **1–3 menit** (tidak perlu download model).

---

### Step 2.5 — Catat URL dan Verifikasi

URL contoh: `https://bank-jatim-backend.ml-xxxxx.cloudera.site`

**Verifikasi dari terminal Workbench session:**
```bash
BACKEND_URL="https://bank-jatim-backend.ml-xxxxx.cloudera.site"

# 1. App health
curl $BACKEND_URL/health
# Expected: {"status":"ok","session_backend":"sqlite","llm_provider":"local_qwen",...}

# 2. Impala connectivity
curl $BACKEND_URL/health/db
# Expected: {"status":"ok","database":"cai_sdx_se_indonesia","result":1}

# 3. ChromaDB collections
curl $BACKEND_URL/rag/options
# Expected: {"enabled":true,"collections":[{"name":"bankjatim_docs","document_count":17}]}

# 4. Full SQL flow test (tunggu ~5-10 detik)
curl -X POST $BACKEND_URL/chat/query \
  -H "Content-Type: application/json" \
  -d '{"question":"Berapa jumlah nasabah per segmen?","session_id":"deploy-test-001"}'
# Expected: JSON dengan answer, generated_sql, rows, visualization
```

> **Simpan URL ini:** `https://bank-jatim-backend.ml-xxxxx.cloudera.site`
> Akan dipakai sebagai `BACKEND_API_BASE_URL` di APP 4.

---

## APP 3 — MCP Server Application

**Tujuan:** Structured analytics tools — sql_query, dormant risk summary, campaign recommendation, RAG search.
**Deploy setelah APP 1 dan APP 2 running.**

---

### Step 3.1 — Buka halaman Applications

1. Di menu kiri, klik **Applications**
2. Klik tombol **New Application**

---

### Step 3.2 — Isi form Application

| Field | Value |
|---|---|
| **Name** | `bank-jatim-mcp-server` |
| **Subdomain** | `bank-jatim-mcp-server` |
| **Description** | `MCP Server — structured tools for customer dormant analytics` |
| **Script** | `bank-jawa-timur/ask-data/mcp_server/mcp_entry.py` |
| **Engine Kernel** | `Python 3.11` |
| **Engine Profile** | CPU — **2 vCPU, 4 GB RAM** |
| **Replicas** | `1` |

Centang: **☑ Enable Unauthenticated Access**

---

### Step 3.3 — Set Environment Variables

| Key | Value |
|---|---|
| `IMPALA_HOST` | `coordinator-default-impala-aws.dw-go01-demo-aws.ylcu-atmi.cloudera.site` |
| `IMPALA_PORT` | `443` |
| `IMPALA_HTTP_PATH` | `cliservice` |
| `CDP_USER` | `triano` |
| `CDP_PASS` | `<cdp-password>` |
| `DB_NAME` | `cai_sdx_se_indonesia` |
| `CHROMA_PERSIST_DIR` | `/home/cdsw/bank-jawa-timur/ask-data/chroma_db` |
| `CHROMA_COLLECTION` | `bankjatim_docs` |
| `EMBED_MODEL` | `nomic-embed-text` |
| `OLLAMA_BASE_URL` | `https://bank-jatim-qwen-llm.ml-xxxxx.cloudera.site` |

---

### Step 3.4 — Deploy

Klik **Create Application**.

Tunggu status `Running`. Biasanya **1–2 menit**.

---

### Step 3.5 — Verifikasi Semua 6 Tools

URL contoh: `https://bank-jatim-mcp-server.ml-xxxxx.cloudera.site`

```bash
MCP_URL="https://bank-jatim-mcp-server.ml-xxxxx.cloudera.site"

# 1. Health check
curl $MCP_URL/health
# Expected: {"status":"ok","service":"mcp-server"}

# 2. List tools
curl $MCP_URL/tools | python3 -m json.tool
# Expected: 6 tools listed

# 3. Tool: sql_query
curl -X POST $MCP_URL/tools/sql_query \
  -H "Content-Type: application/json" \
  -d '{"sql":"SELECT COUNT(*) as total FROM cai_sdx_se_indonesia.customer_dormant_segment"}'
# Expected: {"tool":"sql_query","result":{"rows":[{"total":10000}],...}}

# 4. Tool: dormant_risk_summary
curl -X POST $MCP_URL/tools/dormant_risk_summary \
  -H "Content-Type: application/json" \
  -d '{"risk_level":"HIGH"}'
# Expected: rows dengan dormant_risk_level HIGH, customer_count, percentage

# 5. Tool: dormant_reason_breakdown
curl -X POST $MCP_URL/tools/dormant_reason_breakdown \
  -H "Content-Type: application/json" \
  -d '{"risk_level":"HIGH"}'
# Expected: rows LOW_TRANSACTION_COUNT, NO_DIGITAL_LOGIN, dll

# 6. Tool: campaign_recommendation
curl -X POST $MCP_URL/tools/campaign_recommendation \
  -H "Content-Type: application/json" \
  -d '{"risk_level":"HIGH","limit":3}'
# Expected: rows dengan customer_id, action, channel, priority

# 7. Tool: campaign_summary_by_reason
curl $MCP_URL/tools/campaign_summary_by_reason
# Expected: rows per reason code dengan recommended_action

# 8. Tool: rag_search
curl -X POST $MCP_URL/tools/rag_search \
  -H "Content-Type: application/json" \
  -d '{"query":"strategi retensi nasabah dormant","top_k":2}'
# Expected: 2 results dari bankjatim_docs dengan excerpt dan score
```

---

## APP 4 — Frontend Application

**Tujuan:** Next.js UI — chat interface, visualization chart, RAG config modal.
**Deploy ini TERAKHIR** setelah Backend URL sudah diketahui.

---

### Step 4.1 — Buka halaman Applications

1. Di menu kiri, klik **Applications**
2. Klik tombol **New Application**

---

### Step 4.2 — Isi form Application

| Field | Value |
|---|---|
| **Name** | `bank-jatim-frontend` |
| **Subdomain** | `bank-jatim-frontend` |
| **Description** | `Next.js frontend — Ask Data UI Bank Jawa Timur` |
| **Script** | `bank-jawa-timur/ask-data/frontend/frontend_entry.py` |
| **Engine Kernel** | `Python 3.11` |
| **Engine Profile** | CPU — **2 vCPU, 4 GB RAM** |
| **Replicas** | `1` |

Centang: **☑ Enable Unauthenticated Access**

---

### Step 4.3 — Set Environment Variables

| Key | Value |
|---|---|
| `BACKEND_API_BASE_URL` | `https://bank-jatim-backend.ml-xxxxx.cloudera.site` |

> **Tidak boleh ada trailing slash** di URL Backend.
> Contoh benar: `https://bank-jatim-backend.ml-xxxxx.cloudera.site`
> Contoh salah: `https://bank-jatim-backend.ml-xxxxx.cloudera.site/`

---

### Step 4.4 — Deploy

Klik **Create Application**.

Tunggu status `Running`. Pertama kali akan **3–7 menit** karena `npm install` dan `npm build` dijalankan otomatis oleh `frontend_entry.py`.

Pantau di tab **Logs** — tunggu sampai muncul:
```
info  - Ready in Xs
```

---

### Step 4.5 — Verifikasi End-to-End di Browser

Buka URL Frontend Application di browser.
Contoh: `https://bank-jatim-frontend.ml-xxxxx.cloudera.site`

**Test 1 — Welcome screen:**
- Halaman terbuka, muncul greeting: _"Halo, saya Asisten Analitik Bank Jawa Timur"_ ✅
- Ada 3 starter prompt card ✅

**Test 2 — SQL flow:**
- Klik starter prompt: _"Tampilkan jumlah nasabah berdasarkan customer segment"_
- Tunggu 5–10 detik
- Jawaban muncul dalam Bahasa Indonesia + bar chart otomatis ✅

**Test 3 — RAG flow:**
- Klik tombol **"Knowledge Base"** di topbar
- Modal terbuka, toggle Enable → **Aktif** ✅
- Dropdown collection: pilih `bankjatim_docs (17 chunk)` ✅
- Set top_k ke `3`, klik **Simpan konfigurasi**
- Tombol topbar berubah hijau: **"Knowledge Base Aktif"** ✅
- Ketik pertanyaan: _"Apa strategi retensi nasabah dormant?"_
- Jawaban muncul dengan 3 sumber dokumen PDF di bawahnya ✅

**Test 4 — Guardrails:**
- Ketik: _"tampilkan nomor hp semua nasabah"_
- Harus muncul notice: **Sensitive Data Blocked** ✅

---

## Troubleshooting

### APP 1 — Qwen tidak start / terus Pending
- Pastikan resource profile dipilih yang punya GPU L40 — bukan CPU-only profile
- Di tab Logs, cari error `CUDA out of memory` → turunkan `QWEN_GPU_MEMORY_UTILIZATION` ke `0.80`
- Cari error `Repository not found` → set `HUGGING_FACE_HUB_TOKEN` yang valid
- Cari error `model not found` → pastikan `QWEN_MODEL` diisi persis `Qwen/Qwen2.5-14B-Instruct-AWQ`

### APP 2 — Backend health/db gagal
- Error `TSocket read 0 bytes` atau `Unable to connect` → cek `CDP_USER`, `CDP_PASS`, pastikan network CAI bisa reach Impala host
- Error `CHROMA_ENABLED=true` tapi `/rag/options` return `{"enabled":false}` → `CHROMA_PERSIST_DIR` path salah atau folder kosong

### APP 2 — `/chat/query` timeout atau error 502
- Cek log Backend → biasanya LLM timeout karena `QWEN_BASE_URL` salah (harus ada `/v1`)
- Pastikan APP 1 Qwen sudah `Running` sebelum test APP 2

### APP 3 — MCP tools return error Impala
- Sama dengan APP 2 — cek `CDP_USER`, `CDP_PASS`, `IMPALA_HOST`
- Pastikan `CHROMA_PERSIST_DIR` sama absolute path-nya dengan APP 2

### APP 4 — Blank page atau CORS error
- Pastikan `BACKEND_API_BASE_URL` tidak ada trailing slash
- Pastikan semua 4 Applications sudah centang **"Allow Unauthenticated Access"**
- Buka browser DevTools → Network tab → cari request ke `/api/backend` yang gagal → lihat error detail

### APP 4 — Build lama atau gagal
- Di Logs cari `npm ERR!` → biasanya module missing
- `frontend_entry.py` akan auto install ulang jika `node_modules` belum ada — beri waktu 5–10 menit

---

## Checklist Final

### Persiapan
- [ ] `sync_project.py` dijalankan → code `bank-jawa-timur/ask-data/` tersedia di session
- [ ] `chroma_db/` diupload atau di-ingest → `col.count()` = 17

### APP 1 — Qwen LLM
- [ ] Application dibuat dengan GPU L40 profile
- [ ] Env vars diisi: `QWEN_MODEL`, `QWEN_API_KEY`, `QWEN_MAX_MODEL_LEN`, `QWEN_GPU_MEMORY_UTILIZATION`, `QWEN_TENSOR_PARALLEL_SIZE`
- [ ] Status: **Running**
- [ ] `curl $QWEN_URL/health` → `{"status":"ok"}`
- [ ] `curl $QWEN_URL/v1/chat/completions` → response dari Qwen
- [ ] **URL Qwen dicatat** ← wajib untuk step berikutnya

### APP 2 — Backend
- [ ] Application dibuat dengan CPU 4 vCPU 8 GB
- [ ] `QWEN_BASE_URL` diisi dengan URL Qwen + `/v1`
- [ ] `OLLAMA_BASE_URL` diisi dengan URL Qwen tanpa `/v1`
- [ ] `CHROMA_PERSIST_DIR` diisi dengan absolute path
- [ ] Status: **Running**
- [ ] `/health` → `{"status":"ok"}`
- [ ] `/health/db` → `{"status":"ok","database":"cai_sdx_se_indonesia"}`
- [ ] `/rag/options` → `{"enabled":true,"collections":[{"document_count":17}]}`
- [ ] `/chat/query` → jawaban + SQL + visualization
- [ ] **URL Backend dicatat** ← wajib untuk APP 4

### APP 3 — MCP Server
- [ ] Application dibuat dengan CPU 2 vCPU 4 GB
- [ ] `CHROMA_PERSIST_DIR` sama dengan APP 2
- [ ] Status: **Running**
- [ ] `/health` → `{"status":"ok","service":"mcp-server"}`
- [ ] `/tools` → 6 tools listed
- [ ] `sql_query` tool → COUNT 10000
- [ ] `dormant_risk_summary` tool → rows dengan risk levels
- [ ] `rag_search` tool → 2 hasil dari bankjatim_docs

### APP 4 — Frontend
- [ ] Application dibuat dengan CPU 2 vCPU 4 GB
- [ ] `BACKEND_API_BASE_URL` diisi dengan URL Backend (tanpa trailing slash)
- [ ] Status: **Running**
- [ ] Welcome screen terbuka di browser ✅
- [ ] SQL chat: pertanyaan segmen → jawaban + bar chart ✅
- [ ] RAG modal: collection bankjatim_docs muncul → config tersimpan ✅
- [ ] RAG chat: pertanyaan strategi dormant → jawaban + sumber PDF ✅
- [ ] Guardrails: pertanyaan PII → blocked notice ✅
