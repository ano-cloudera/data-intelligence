# CAI Deployment Guide — Bank Jawa Timur PoC

Deploy urutan wajib: **Step 0 Credential → Persiapan → APP 1 Qwen LLM → APP 2 Backend → APP 3 MCP Server → APP 4 Frontend**

---

## Step 0 — Kumpulkan Semua Credential (Lakukan Sebelum Apapun)

Sebelum mulai deploy, pastikan semua credential dan token berikut sudah di tangan.
Simpan di tempat yang aman (password manager atau catatan lokal) — akan dipakai berulang kali di step berikutnya.

---

### 0.1 — HuggingFace Token (untuk download model Qwen)

**Fungsi:** Download model `Qwen/Qwen2.5-14B-Instruct-AWQ` (~8 GB) ke cache CAI session.

**Cara mendapatkan:**

1. Buka [huggingface.co](https://huggingface.co) → login atau daftar akun
2. Klik avatar profil kanan atas → **Settings**
3. Di menu kiri, klik **Access Tokens**
4. Klik tombol **New token**
5. Isi:
   - Name: `cai-bjt-deploy` (bebas)
   - Token type: **Read**
6. Klik **Generate a token**
7. Salin token — tampil sekali, simpan sekarang

```
HUGGING_FACE_HUB_TOKEN = hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

> Token harus punya akses **Read** — cukup untuk download model publik seperti Qwen.
> Model Qwen/Qwen2.5-14B-Instruct-AWQ adalah model publik, tidak butuh akses khusus.

---

### 0.2 — CDP / Impala Credentials (untuk koneksi ke Cloudera Data Warehouse)

**Fungsi:** Autentikasi ke Impala CDW — dipakai oleh Backend (APP 2) dan MCP Server (APP 3).

**Nilai yang sudah diketahui untuk environment ini:**

| Credential | Value |
|---|---|
| `IMPALA_HOST` | `coordinator-default-impala-aws.dw-go01-demo-aws.ylcu-atmi.cloudera.site` |
| `IMPALA_PORT` | `443` |
| `IMPALA_HTTP_PATH` | `cliservice` |
| `DB_NAME` | `cai_sdx_se_indonesia` |
| `CDP_USER` | username CDP kamu (contoh: `triano`) |
| `CDP_PASS` | password CDP kamu |

**Cara verifikasi CDP credentials:**

1. Login ke Cloudera Data Platform (CDP) console
2. Pastikan user kamu punya akses ke Virtual Warehouse `default-impala-aws`
3. Di menu **Data Warehouse** → **Virtual Warehouses** → klik titik tiga → **Copy JDBC URL**
   - Format: `jdbc:impala://<host>:443/;transportMode=http;httpPath=cliservice;ssl=1`
   - Ambil nilai `host` dari URL tersebut sebagai `IMPALA_HOST`

> Jika password CDP expired atau belum diset, hubungi admin CDP untuk reset password.

---

### 0.3 — Qwen API Key (token internal antar Application)

**Fungsi:** Autentikasi antara Backend/MCP Server dan Qwen LLM Application.
Ini **bukan** token publik — bebas diisi string apapun, asalkan konsisten di semua Application.

```
QWEN_API_KEY = local-dev-token
```

> Gunakan nilai di atas. Jika mau diganti, pastikan diisi **sama persis** di APP 1, APP 2, dan APP 3.

---

### 0.4 — Ringkasan Credential untuk Disimpan

Isi tabel ini sebelum mulai deploy:

| Credential | Value | Dipakai di |
|---|---|---|
| `HUGGING_FACE_HUB_TOKEN` | `hf_xxx...` | Step B (download model) |
| `IMPALA_HOST` | `coordinator-default-impala-aws...` | APP 2, APP 3 |
| `IMPALA_PORT` | `443` | APP 2, APP 3 |
| `IMPALA_HTTP_PATH` | `cliservice` | APP 2, APP 3 |
| `CDP_USER` | username CDP | APP 2, APP 3 |
| `CDP_PASS` | password CDP | APP 2, APP 3 |
| `DB_NAME` | `cai_sdx_se_indonesia` | APP 2, APP 3 |
| `QWEN_API_KEY` | `local-dev-token` | APP 1, APP 2, APP 3 |
| `QWEN_MODEL` | `Qwen/Qwen2.5-14B-Instruct-AWQ` | APP 1, APP 2 |
| URL APP 1 (Qwen) | `https://bjt-ask-data-qwen.ml-xxxxx.cloudera.site` | APP 2, APP 3 (setelah APP 1 running) |
| URL APP 2 (Backend) | `https://bjt-ask-data-backend.ml-xxxxx.cloudera.site` | APP 4 (setelah APP 2 running) |

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

### Step B — Download Model Qwen ke Cache Session

Download model **sebelum** deploy APP 1 supaya Application start tanpa perlu menunggu download (8–9 GB).
Jalankan di **Workbench session** (bukan Application).

**1. Set HuggingFace token di terminal session:**

```bash
export HUGGING_FACE_HUB_TOKEN=hf_xxxxxxxxxxxxxxxx
```

> Buat token di [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) — pilih tipe **Read**.

**2. Jalankan script download:**

```bash
python bank-jawa-timur/ask-data/qwen_inference/download_model.py
```

Output yang diharapkan:

```text
INFO Model download: Qwen/Qwen2.5-14B-Instruct-AWQ
INFO Cache dir: ~/.cache/huggingface/hub (default)
...
INFO Download complete. Local path: /home/cdsw/.cache/huggingface/hub/models--Qwen--Qwen2.5-14B-Instruct-AWQ/...
INFO Found cached model: Qwen/Qwen2.5-14B-Instruct-AWQ (8.xx GB, 1 revision(s))
INFO Model ready. You can now deploy the Qwen LLM Application.
```

**3. Verifikasi cache:**

```bash
du -sh ~/.cache/huggingface/hub/models--Qwen--Qwen2.5-14B-Instruct-AWQ/
# Expected: ~8-9G
```

> Setelah model ter-cache, `HUGGING_FACE_HUB_TOKEN` **tidak perlu** diisi di env vars Application.

**Opsional — Download model yang lebih kecil (jika VRAM terbatas):**

```bash
export QWEN_MODEL=Qwen/Qwen2.5-7B-Instruct-AWQ
python bank-jawa-timur/ask-data/qwen_inference/download_model.py
# ~4 GB, cocok untuk 1 GPU L40 dengan headroom lebih besar
```

---

### Step C — Siapkan ChromaDB (Vector Store)

ChromaDB tidak di-commit ke git, harus disiapkan manual.

**Option 1 — Upload dari lokal (lebih cepat, sudah ada 17 chunks):**

File `chroma_db.zip` sudah disiapkan di folder `ask-data/` lokal.
Upload file tersebut ke CAI Workbench session via **File Upload UI** (ikon upload di file browser session), lalu di terminal session:

```bash
# Pindah ke folder project
cd /home/cdsw/bank-jawa-timur/ask-data

# Extract zip (file ada di home dir setelah upload)
unzip ~/chroma_db.zip

# Verifikasi struktur
ls chroma_db/
# Harus ada: chroma.sqlite3 dan subfolder UUID (33d4a0a6-...)
```

**Option 2 — Ingest PDF langsung dari repo (recommended jika sudah sync):**

PDF sudah ada di repo di `ask-data/data/documents/` — tidak perlu upload manual.
Setelah `sync_project.py` dijalankan (Step A), langsung jalankan:

```bash
cd /home/cdsw/bank-jawa-timur/ask-data
pip install -r backend/requirements.txt -q
PYTHONPATH=backend python scripts/ingest_documents.py
# Expected output:
# Ingesting: 01_strategi_customer_segmentation_portfolio_bank_jatim.pdf ... X chunks
# Ingesting: 02_dormant_customer_retention_strategy_bank_jatim.pdf ... X chunks
# ...
# Done. Total chunks ingested: 17
```

**Verifikasi ChromaDB:**

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
| **Name** | `bjt-ask-data-qwen` |
| **Subdomain** | `bjt-ask-data-qwen` _(auto-fill, bisa dibiarkan)_ |
| **Description** | `Qwen2.5-14B-Instruct-AWQ via vLLM — LLM inference server` |
| **Script** | `bank-jawa-timur/ask-data/qwen_inference/qwen_entry.py` |
| **Engine Kernel** | `Python 3.11` |
| **Engine Profile** | Pilih profile GPU dengan **NVIDIA L40** — minimal 1 GPU, 48 GB VRAM |
| **Replicas** | `1` |

Centang: **☑ Enable Unauthenticated Access**

---

### Step 1.3 — Set Environment Variables

Klik tab **Environment Variables**, tambahkan:

| Key | Value | Keterangan |
|---|---|---|
| `QWEN_MODEL` | `Qwen/Qwen2.5-14B-Instruct-AWQ` | Harus cocok dengan model yang didownload di Step B |
| `QWEN_API_KEY` | `local-dev-token` | Token autentikasi internal |
| `QWEN_MAX_MODEL_LEN` | `8192` | Max context window (token) |
| `QWEN_GPU_MEMORY_UTILIZATION` | `0.90` | 90% VRAM L40 (bisa turunkan ke 0.85 jika 2 GPU) |
| `QWEN_TENSOR_PARALLEL_SIZE` | `1` | Set ke `2` jika pakai kedua GPU L40 |

> **Jika model belum ter-cache** (skip Step B), tambahkan juga:
> `HUGGING_FACE_HUB_TOKEN` = `hf_xxxxxxxxxxxxxxxx`
>
> **Jika pakai 2 GPU L40**, set:
> `QWEN_TENSOR_PARALLEL_SIZE` = `2` dan `QWEN_GPU_MEMORY_UTILIZATION` = `0.85`

---

### Step 1.4 — Deploy

Klik **Create Application**.

Tunggu status berubah dari `Starting` → `Running`.

- Jika model sudah ter-cache (Step B): **2–5 menit**
- Jika model belum ter-cache (download saat start): **15–30 menit**

Pantau progress di tab **Logs** Application.

---

### Step 1.5 — Catat URL dan Verifikasi

Setelah status `Running`, klik nama Application untuk lihat URL-nya.
Contoh URL: `https://bjt-ask-data-qwen.ml-xxxxx.cloudera.site`

Verifikasi dari terminal Workbench session:

```bash
QWEN_URL="https://bjt-ask-data-qwen.ml-xxxxx.cloudera.site"

# Test vLLM models list
curl $QWEN_URL/v1/models \
  -H "Authorization: Bearer local-dev-token"
# Expected: {"object":"list","data":[{"id":"Qwen/Qwen2.5-14B-Instruct-AWQ",...}]}

# Test chat completions
curl -X POST $QWEN_URL/v1/chat/completions \
  -H "Authorization: Bearer local-dev-token" \
  -H "Content-Type: application/json" \
  -d '{"model":"Qwen/Qwen2.5-14B-Instruct-AWQ","messages":[{"role":"user","content":"Halo, siapa kamu?"}],"max_tokens":50}'
# Expected: response JSON dengan content jawaban dari Qwen
```

> **Simpan URL ini** → akan dipakai sebagai `QWEN_BASE_URL` dan `OLLAMA_BASE_URL` di APP 2 & 3.

---

## APP 2 — Backend Application

**Tujuan:** FastAPI server — SQL generation, Impala query execution, ChromaDB RAG, session management.
**Deploy setelah APP 1 Running.**

---

### Step 2.1 — Buka halaman Applications

1. Di menu kiri, klik **Applications**
2. Klik tombol **New Application**

---

### Step 2.2 — Isi form Application

| Field | Value |
|---|---|
| **Name** | `bjt-ask-data-backend` |
| **Subdomain** | `bjt-ask-data-backend` |
| **Description** | `FastAPI backend — NL to SQL, ChromaDB RAG, Impala CDW` |
| **Script** | `bank-jawa-timur/ask-data/backend/backend_entry.py` |
| **Engine Kernel** | `Python 3.11` |
| **Engine Profile** | CPU — **4 vCPU, 8 GB RAM** |
| **Replicas** | `1` |

Centang: **☑ Enable Unauthenticated Access**

---

### Step 2.3 — Set Environment Variables

| Key | Value | Keterangan |
|---|---|---|
| `LLM_PROVIDER` | `local_qwen` | Aktifkan Qwen sebagai LLM provider |
| `QWEN_BASE_URL` | `https://bjt-ask-data-qwen.ml-xxxxx.cloudera.site/v1` | URL APP 1 + `/v1` |
| `QWEN_API_KEY` | `local-dev-token` | Sama dengan yang diset di APP 1 |
| `QWEN_MODEL` | `Qwen/Qwen2.5-14B-Instruct-AWQ` | Sama dengan yang diset di APP 1 |
| `IMPALA_HOST` | `coordinator-default-impala-aws.dw-go01-demo-aws.ylcu-atmi.cloudera.site` | Impala CDW host |
| `IMPALA_PORT` | `443` | Port HTTPS |
| `IMPALA_HTTP_PATH` | `cliservice` | HTTP path Impala |
| `CDP_USER` | `triano` | CDP username |
| `CDP_PASS` | `<cdp-password>` | CDP password |
| `DB_NAME` | `cai_sdx_se_indonesia` | Database Impala |
| `SESSION_BACKEND` | `sqlite` | Simpan sesi di SQLite lokal |
| `SESSION_SQLITE_PATH` | `data/ask_data_sessions.db` | Path file SQLite |
| `SESSION_TTL_MINUTES` | `60` | Sesi expired setelah 60 menit |
| `MEMORY_MAX_HISTORY` | `10` | Max pesan history per sesi |
| `GUARDRAILS_ENABLED` | `true` | Aktifkan PII blocking |
| `CHROMA_ENABLED` | `true` | Aktifkan ChromaDB RAG |
| `CHROMA_PERSIST_DIR` | `/home/cdsw/bank-jawa-timur/ask-data/chroma_db` | Path absolut ChromaDB |
| `CHROMA_COLLECTION` | `bankjatim_docs` | Nama collection |
| `EMBED_MODEL` | `nomic-embed-text` | Embedding model via Ollama |
| `OLLAMA_BASE_URL` | `https://bjt-ask-data-qwen.ml-xxxxx.cloudera.site` | URL APP 1 **tanpa** `/v1` |

> **Penting:**
> - `QWEN_BASE_URL` = URL Qwen App + `/v1` di akhir
> - `OLLAMA_BASE_URL` = URL Qwen App **tanpa** `/v1`
> - `CHROMA_PERSIST_DIR` = absolute path `/home/cdsw/...`, bukan `./chroma_db`

---

### Step 2.4 — Deploy

Klik **Create Application**.

Tunggu status `Running`. Biasanya **1–3 menit** (tidak perlu download model).

---

### Step 2.5 — Catat URL dan Verifikasi

URL contoh: `https://bjt-ask-data-backend.ml-xxxxx.cloudera.site`

```bash
BACKEND_URL="https://bjt-ask-data-backend.ml-xxxxx.cloudera.site"

# 1. App health
curl $BACKEND_URL/health
# Expected: {"status":"ok","session_backend":"sqlite","llm_provider":"local_qwen",...}

# 2. Impala connectivity
curl $BACKEND_URL/health/db
# Expected: {"status":"ok","database":"cai_sdx_se_indonesia","result":1}

# 3. ChromaDB collections
curl $BACKEND_URL/rag/options
# Expected: {"enabled":true,"collections":[{"name":"bankjatim_docs","document_count":17}]}

# 4. Full SQL flow test (tunggu ~5-10 detik pertama kali)
curl -X POST $BACKEND_URL/chat/query \
  -H "Content-Type: application/json" \
  -d '{"question":"Berapa jumlah nasabah per segmen?","session_id":"deploy-test-001"}'
# Expected: JSON dengan answer, generated_sql, rows, visualization
```

> **Simpan URL ini** → akan dipakai sebagai `BACKEND_API_BASE_URL` di APP 4.

---

## APP 3 — MCP Server Application

**Tujuan:** Structured analytics tools — sql_query, dormant risk summary, campaign recommendation, RAG search.
**Deploy setelah APP 1 Running.**

---

### Step 3.1 — Buka halaman Applications

1. Di menu kiri, klik **Applications**
2. Klik tombol **New Application**

---

### Step 3.2 — Isi form Application

| Field | Value |
|---|---|
| **Name** | `bjt-ask-data-mcp` |
| **Subdomain** | `bjt-ask-data-mcp` |
| **Description** | `MCP Server — structured tools for customer dormant analytics` |
| **Script** | `bank-jawa-timur/ask-data/mcp_server/mcp_entry.py` |
| **Engine Kernel** | `Python 3.11` |
| **Engine Profile** | CPU — **2 vCPU, 4 GB RAM** |
| **Replicas** | `1` |

Centang: **☑ Enable Unauthenticated Access**

---

### Step 3.3 — Set Environment Variables

| Key | Value | Keterangan |
|---|---|---|
| `IMPALA_HOST` | `coordinator-default-impala-aws.dw-go01-demo-aws.ylcu-atmi.cloudera.site` | Impala CDW host |
| `IMPALA_PORT` | `443` | Port HTTPS |
| `IMPALA_HTTP_PATH` | `cliservice` | HTTP path Impala |
| `CDP_USER` | `triano` | CDP username |
| `CDP_PASS` | `<cdp-password>` | CDP password |
| `DB_NAME` | `cai_sdx_se_indonesia` | Database Impala |
| `CHROMA_PERSIST_DIR` | `/home/cdsw/bank-jawa-timur/ask-data/chroma_db` | **Harus sama** dengan APP 2 |
| `CHROMA_COLLECTION` | `bankjatim_docs` | Nama collection |
| `EMBED_MODEL` | `nomic-embed-text` | Embedding model via Ollama |
| `OLLAMA_BASE_URL` | `https://bjt-ask-data-qwen.ml-xxxxx.cloudera.site` | URL APP 1 tanpa `/v1` |

---

### Step 3.4 — Deploy

Klik **Create Application**.

Tunggu status `Running`. Biasanya **1–2 menit**.

---

### Step 3.5 — Verifikasi Semua 6 Tools

URL contoh: `https://bjt-ask-data-mcp.ml-xxxxx.cloudera.site`

```bash
MCP_URL="https://bjt-ask-data-mcp.ml-xxxxx.cloudera.site"

# 1. Health check
curl $MCP_URL/health
# Expected: {"status":"ok","service":"mcp-server"}

# 2. List tools (harus ada 6)
curl $MCP_URL/tools | python3 -m json.tool

# 3. sql_query — count total nasabah
curl -X POST $MCP_URL/tools/sql_query \
  -H "Content-Type: application/json" \
  -d '{"sql":"SELECT COUNT(*) as total FROM cai_sdx_se_indonesia.customer_dormant_segment"}'
# Expected: {"tool":"sql_query","result":{"rows":[{"total":10000}],...}}

# 4. dormant_risk_summary
curl -X POST $MCP_URL/tools/dormant_risk_summary \
  -H "Content-Type: application/json" \
  -d '{"risk_level":"HIGH"}'
# Expected: rows dengan dormant_risk_level HIGH, customer_count, percentage

# 5. dormant_reason_breakdown
curl -X POST $MCP_URL/tools/dormant_reason_breakdown \
  -H "Content-Type: application/json" \
  -d '{"risk_level":"HIGH"}'
# Expected: rows LOW_TRANSACTION_COUNT, NO_DIGITAL_ACTIVITY, dll

# 6. campaign_recommendation
curl -X POST $MCP_URL/tools/campaign_recommendation \
  -H "Content-Type: application/json" \
  -d '{"risk_level":"HIGH","limit":3}'
# Expected: rows dengan customer_id, action, channel, priority

# 7. campaign_summary_by_reason
curl $MCP_URL/tools/campaign_summary_by_reason
# Expected: rows per reason code dengan recommended_action

# 8. rag_search
curl -X POST $MCP_URL/tools/rag_search \
  -H "Content-Type: application/json" \
  -d '{"query":"strategi retensi nasabah dormant","top_k":2}'
# Expected: 2 results dari bankjatim_docs dengan excerpt dan score
```

---

## APP 4 — Frontend Application

**Tujuan:** Next.js UI — chat interface, visualization chart, RAG config modal.
**Deploy ini TERAKHIR** setelah URL Backend sudah diketahui.

---

### Step 4.1 — Buka halaman Applications

1. Di menu kiri, klik **Applications**
2. Klik tombol **New Application**

---

### Step 4.2 — Isi form Application

| Field | Value |
|---|---|
| **Name** | `bjt-ask-data-frontend` |
| **Subdomain** | `bjt-ask-data-frontend` |
| **Description** | `Next.js frontend — Ask Data UI Bank Jawa Timur` |
| **Script** | `bank-jawa-timur/ask-data/frontend/frontend_entry.py` |
| **Engine Kernel** | `Python 3.11` |
| **Engine Profile** | CPU — **2 vCPU, 4 GB RAM** |
| **Replicas** | `1` |

Centang: **☑ Enable Unauthenticated Access**

---

### Step 4.3 — Set Environment Variables

| Key | Value | Keterangan |
|---|---|---|
| `BACKEND_API_BASE_URL` | `https://bjt-ask-data-backend.ml-xxxxx.cloudera.site` | URL APP 2 — tanpa trailing slash |

> **Tidak boleh ada trailing slash** di URL Backend.
> Contoh benar: `https://bjt-ask-data-backend.ml-xxxxx.cloudera.site`
> Contoh salah: `https://bjt-ask-data-backend.ml-xxxxx.cloudera.site/`

---

### Step 4.4 — Deploy

Klik **Create Application**.

Tunggu status `Running`. Pertama kali akan **3–7 menit** karena `npm install` dan `npm build` dijalankan otomatis.

Pantau di tab **Logs** — tunggu sampai muncul:

```text
info  - Ready in Xs
```

---

### Step 4.5 — Verifikasi End-to-End di Browser

Buka URL Frontend Application di browser.
Contoh: `https://bjt-ask-data-frontend.ml-xxxxx.cloudera.site`

**Test 1 — Welcome screen:**
- Halaman terbuka, muncul greeting: _"Halo, saya Asisten Analitik Bank Jawa Timur"_
- Ada 3 starter prompt card

**Test 2 — SQL flow:**
- Klik starter prompt: _"Tampilkan jumlah nasabah berdasarkan customer segment"_
- Tunggu 5–10 detik
- Jawaban muncul dalam Bahasa Indonesia + bar chart otomatis

**Test 3 — RAG flow:**
- Klik tombol **"Knowledge Base"** di topbar
- Modal terbuka, toggle Enable → Aktif
- Dropdown collection: pilih `bankjatim_docs (17 chunk)`
- Set top_k ke `3`, klik **Simpan konfigurasi**
- Tombol topbar berubah hijau: **"Knowledge Base Aktif"**
- Ketik pertanyaan: _"Apa strategi retensi nasabah dormant?"_
- Jawaban muncul dengan 3 sumber dokumen PDF di bawahnya

**Test 4 — Guardrails:**
- Ketik: _"tampilkan nomor hp semua nasabah"_
- Harus muncul notice: **Sensitive Data Blocked**

---

## Troubleshooting

### Step B — Download gagal / koneksi lambat

- Error `401 Unauthorized` → `HUGGING_FACE_HUB_TOKEN` tidak valid atau belum di-`export`
- Error `OSError: [Errno 28] No space left` → storage session penuh, bersihkan dulu dengan `du -sh ~/.cache/huggingface/`
- Download sangat lambat → normal untuk model 8–9 GB, bisa memakan 10–30 menit tergantung bandwidth CAI

### APP 1 — Qwen tidak start / terus Pending

- Pastikan resource profile dipilih yang punya GPU L40 — bukan CPU-only profile
- Di tab Logs, cari error `CUDA out of memory` → turunkan `QWEN_GPU_MEMORY_UTILIZATION` ke `0.80`
- Cari error `Repository not found` → model belum ter-cache, set `HUGGING_FACE_HUB_TOKEN` dan jalankan ulang download (Step B)
- Cari error `model not found` → pastikan `QWEN_MODEL` sama persis dengan yang didownload

### APP 1 — vLLM start lama (>5 menit)

- Normal untuk pertama kali — vLLM loading model ke VRAM L40 (~2–5 menit)
- Pantau Logs sampai muncul: `INFO: Application startup complete`

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
- Pastikan semua 4 Applications sudah centang **"Enable Unauthenticated Access"**
- Buka browser DevTools → Network tab → cari request yang gagal → lihat error detail

### APP 4 — Build lama atau gagal

- Di Logs cari `npm ERR!` → biasanya module missing
- `frontend_entry.py` akan auto install ulang jika `node_modules` belum ada — beri waktu 5–10 menit

---

## Checklist Final

### Persiapan

- [ ] `sync_project.py` dijalankan → folder `bank-jawa-timur/ask-data/` tersedia di session
- [ ] `download_model.py` dijalankan → model ter-cache di `~/.cache/huggingface/hub/models--Qwen--Qwen2.5-14B-Instruct-AWQ/` (~8–9 GB)
- [ ] ChromaDB disiapkan → `col.count()` = 17

### APP 1 — Qwen LLM (`bjt-ask-data-qwen`)

- [ ] Application name: `bjt-ask-data-qwen`, subdomain: `bjt-ask-data-qwen`
- [ ] Script: `bank-jawa-timur/ask-data/qwen_inference/qwen_entry.py`
- [ ] Engine Profile: GPU L40, Python 3.11
- [ ] Env vars diisi: `QWEN_MODEL`, `QWEN_API_KEY`, `QWEN_MAX_MODEL_LEN`, `QWEN_GPU_MEMORY_UTILIZATION`, `QWEN_TENSOR_PARALLEL_SIZE`
- [ ] Enable Unauthenticated Access: ☑
- [ ] Status: **Running**
- [ ] `curl https://bjt-ask-data-qwen.ml-xxxxx.cloudera.site/v1/models` → model ID terdaftar
- [ ] `curl .../v1/chat/completions` → response dari Qwen
- [ ] **URL `https://bjt-ask-data-qwen.ml-xxxxx.cloudera.site` dicatat** ← wajib untuk APP 2 & 3

### APP 2 — Backend (`bjt-ask-data-backend`)

- [ ] Application name: `bjt-ask-data-backend`, subdomain: `bjt-ask-data-backend`
- [ ] Script: `bank-jawa-timur/ask-data/backend/backend_entry.py`
- [ ] Engine Profile: CPU 4 vCPU 8 GB, Python 3.11
- [ ] `QWEN_BASE_URL` = `https://bjt-ask-data-qwen.ml-xxxxx.cloudera.site/v1`
- [ ] `OLLAMA_BASE_URL` = `https://bjt-ask-data-qwen.ml-xxxxx.cloudera.site`
- [ ] `CHROMA_PERSIST_DIR` = `/home/cdsw/bank-jawa-timur/ask-data/chroma_db`
- [ ] Enable Unauthenticated Access: ☑
- [ ] Status: **Running**
- [ ] `/health` → `{"status":"ok"}`
- [ ] `/health/db` → `{"status":"ok","database":"cai_sdx_se_indonesia"}`
- [ ] `/rag/options` → `{"enabled":true,"collections":[{"document_count":17}]}`
- [ ] `/chat/query` → jawaban + SQL + visualization
- [ ] **URL `https://bjt-ask-data-backend.ml-xxxxx.cloudera.site` dicatat** ← wajib untuk APP 4

### APP 3 — MCP Server (`bjt-ask-data-mcp`)

- [ ] Application name: `bjt-ask-data-mcp`, subdomain: `bjt-ask-data-mcp`
- [ ] Script: `bank-jawa-timur/ask-data/mcp_server/mcp_entry.py`
- [ ] Engine Profile: CPU 2 vCPU 4 GB, Python 3.11
- [ ] `CHROMA_PERSIST_DIR` = `/home/cdsw/bank-jawa-timur/ask-data/chroma_db` (sama dengan APP 2)
- [ ] Enable Unauthenticated Access: ☑
- [ ] Status: **Running**
- [ ] `/health` → `{"status":"ok","service":"mcp-server"}`
- [ ] `/tools` → 6 tools terdaftar
- [ ] `sql_query` → COUNT 10000
- [ ] `dormant_risk_summary` → rows dengan risk levels
- [ ] `rag_search` → 2 hasil dari bankjatim_docs

### APP 4 — Frontend (`bjt-ask-data-frontend`)

- [ ] Application name: `bjt-ask-data-frontend`, subdomain: `bjt-ask-data-frontend`
- [ ] Script: `bank-jawa-timur/ask-data/frontend/frontend_entry.py`
- [ ] Engine Profile: CPU 2 vCPU 4 GB, Python 3.11
- [ ] `BACKEND_API_BASE_URL` = `https://bjt-ask-data-backend.ml-xxxxx.cloudera.site` (tanpa trailing slash)
- [ ] Enable Unauthenticated Access: ☑
- [ ] Status: **Running**
- [ ] Welcome screen terbuka di browser
- [ ] SQL chat: pertanyaan segmen → jawaban + bar chart
- [ ] RAG modal: collection bankjatim_docs muncul → config tersimpan
- [ ] RAG chat: pertanyaan strategi dormant → jawaban + sumber PDF
- [ ] Guardrails: pertanyaan PII → blocked notice
