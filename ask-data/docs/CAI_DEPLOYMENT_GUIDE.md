# CAI Deployment Guide — Ask Data (Customer Dormant Segment Analytics)

> **Panduan ini berlaku untuk deployment di environment CAI manapun.**
> Semua nilai seperti hostname Impala, nama database, subdomain, URL, dan credential
> wajib disesuaikan dengan environment target sebelum deploy.

Deploy urutan wajib:
**Step 0 Credential → Persiapan (A–D) → APP 1 Qwen LLM → APP 2 Backend → APP 3 MCP Server → APP 4 Frontend**

---

## Prerequisite

### Runtime & Infrastruktur

| Komponen | Spesifikasi |
|---|---|
| Cloudera AI (CAI) Workbench | 2025.x (CML runtime) |
| Python | 3.10 atau 3.11 (tersedia di CAI runtime) |
| Node.js & npm | Tersedia di CAI runtime (dipakai oleh APP 4) |
| GPU (untuk APP 1) | NVIDIA L4 (22 GB VRAM) — minimum 1 unit |
| CUDA | 12.x (tersedia di CAI GPU runtime) |

### Akses Eksternal

| Akses | Keterangan |
|---|---|
| Cloudera Data Warehouse (Impala) | Virtual Warehouse aktif, user punya akses ke database target |
| HuggingFace | Internet dari CAI session bisa reach `huggingface.co` (download model ~8–9 GB) |
| GitHub | Internet bisa reach `github.com` (untuk `git clone`) |

### Resource per Application

| Application | CPU | RAM | GPU | Waktu Start |
|---|---|---|---|---|
| APP 1 — Qwen LLM | 4 vCPU | 16 GiB | 1× GPU (≥22 GB VRAM) | 3–5 menit |
| APP 2 — Backend | 4 vCPU | 8 GiB | — | 1–3 menit |
| APP 3 — MCP Server | 2 vCPU | 4 GiB | — | 1–2 menit |
| APP 4 — Frontend | 2 vCPU | 4 GiB | — | 3–7 menit |
| **Total** | **12 vCPU** | **32 GiB** | **1 GPU** | |

### Dependencies per Application

Dependencies **diinstall otomatis** oleh masing-masing entry script saat Application pertama start.
Tidak perlu install manual di dalam Application.

**APP 1 — Qwen LLM** (pre-install di Workbench session, bukan di Application — lihat Step D):

| Package | Versi |
|---|---|
| `vllm` | 0.7.3 |
| `torch` | 2.5.1 |
| `transformers` | 4.51.3 |
| `tokenizers` | ≥0.19.0, <0.22 |
| `accelerate` | ≥0.34.0 |
| `huggingface_hub` | ≥0.24.0 |

**APP 2 — Backend** (diinstall dari `backend/requirements.txt`):

| Package | Versi |
|---|---|
| `fastapi` | 0.127.0 |
| `uvicorn` | 0.30.6 |
| `pydantic` | 2.9.2 |
| `impyla` | 0.19.0 |
| `chromadb` | ≥0.5.0 |
| `pysqlite3-binary` | ≥0.5.0 |
| `openai` | 1.51.2 |
| `httpx` | 0.27.2 |
| `ollama` | ≥0.3.0 |
| `pypdf` | ≥4.0.0 |
| `boto3` | 1.42.97 |

**APP 3 — MCP Server** (diinstall dari `mcp_server/requirements.txt`):

| Package | Versi |
|---|---|
| `fastapi` | 0.127.0 |
| `uvicorn` | 0.30.6 |
| `pydantic` | 2.9.2 |
| `impyla` | 0.19.0 |
| `chromadb` | ≥0.5.0 |
| `pysqlite3-binary` | ≥0.5.0 |
| `ollama` | ≥0.3.0 |

**APP 4 — Frontend** (diinstall via `npm install` dari `frontend/package.json`):

| Package | Keterangan |
|---|---|
| `next` | Next.js 15 |
| `react`, `react-dom` | React 18 |
| `recharts` | Chart library |
| `@mui/icons-material`, `@mui/material` | MUI icons & components |
| `@emotion/react`, `@emotion/styled` | MUI styling |
| `tailwindcss` | Utility CSS |

---

## Step 0 — Kumpulkan Semua Credential

Isi semua nilai berikut **sebelum mulai deploy**. Simpan di password manager atau catatan lokal — akan dipakai berulang kali.

### 0.1 — HuggingFace Token

Dipakai untuk download model Qwen (~8–9 GB) ke cache Workbench session.

1. Buka [huggingface.co](https://huggingface.co) → login → **Settings** → **Access Tokens**
2. Klik **New token** → Type: **Read** → Generate
3. Salin token — tampil sekali saja

```
HUGGING_FACE_HUB_TOKEN = hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

> Model Qwen2.5-x-Instruct-AWQ adalah model publik — token Read sudah cukup.
> Setelah model ter-cache di session, token **tidak perlu** diset di Application env vars.

---

### 0.2 — Impala / CDP Credentials

Dipakai oleh APP 2 (Backend) dan APP 3 (MCP Server) untuk query ke Cloudera Data Warehouse.

Cari nilai-nilai ini di Cloudera Data Platform console:

- **IMPALA_HOST** — dari JDBC URL Virtual Warehouse:
  `Data Warehouse → Virtual Warehouses → ⋮ → Copy JDBC URL`
  Format: `jdbc:impala://<host>:443/;transportMode=http;httpPath=cliservice;ssl=1`
  → Ambil bagian `<host>`

- **IMPALA_PORT** — biasanya `443`
- **IMPALA_HTTP_PATH** — biasanya `cliservice`
- **DB_NAME** — nama database Impala yang berisi tabel `customer_dormant_segment`
- **CDP_USER** — username CDP kamu
- **CDP_PASS** — password CDP kamu

```
IMPALA_HOST      = <hostname-impala-virtual-warehouse>
IMPALA_PORT      = 443
IMPALA_HTTP_PATH = cliservice
DB_NAME          = <nama-database-impala>
CDP_USER         = <cdp-username>
CDP_PASS         = <cdp-password>
```

---

### 0.3 — Qwen API Key (Internal Token)

Token internal antar Application — bukan token publik. Bebas diisi string apapun, asalkan **sama persis** di APP 1, APP 2, dan APP 3.

```
QWEN_API_KEY = <pilih-string-rahasia-kamu>
```

---

### 0.4 — Model yang Digunakan

| Parameter | Default | Keterangan |
|---|---|---|
| `QWEN_MODEL` | `Qwen/Qwen2.5-14B-Instruct-AWQ` | HuggingFace model ID — bisa diganti ke versi lain |

**Opsi model alternatif** (jika VRAM terbatas):

| Model | Ukuran download | VRAM |
|---|---|---|
| `Qwen/Qwen2.5-14B-Instruct-AWQ` | ~8.5 GB | ~18 GB _(recommended)_ |
| `Qwen/Qwen2.5-7B-Instruct-AWQ` | ~4 GB | ~10 GB |
| `Qwen/Qwen2.5-3B-Instruct-AWQ` | ~2 GB | ~5 GB |

Nilai `QWEN_MODEL` yang sama **wajib identik** di APP 1 dan APP 2.

---

### 0.5 — Ringkasan Credential

Isi tabel ini sebelum deploy:

| Credential | Nilai | Dipakai di |
|---|---|---|
| `HUGGING_FACE_HUB_TOKEN` | `hf_xxx...` | Step B |
| `IMPALA_HOST` | `<impala-host>` | APP 2, APP 3 |
| `IMPALA_PORT` | `443` | APP 2, APP 3 |
| `IMPALA_HTTP_PATH` | `cliservice` | APP 2, APP 3 |
| `DB_NAME` | `<nama-database>` | APP 2, APP 3 |
| `CDP_USER` | `<username>` | APP 2, APP 3 |
| `CDP_PASS` | `<password>` | APP 2, APP 3 |
| `QWEN_API_KEY` | `<secret-token>` | APP 1, APP 2, APP 3 |
| `QWEN_MODEL` | `Qwen/Qwen2.5-14B-Instruct-AWQ` | APP 1, APP 2 |
| URL APP 1 | _(catat setelah APP 1 running)_ | APP 2, APP 3 |
| URL APP 2 | _(catat setelah APP 2 running)_ | APP 4 |

---

## Persiapan — Lakukan Sekali Sebelum Deploy

### Step A — Clone Repo ke Workbench Session

Buka terminal di CAI Workbench session:

**Jika pertama kali:**

```bash
cd /home/cdsw
git clone https://github.com/ano-cloudera/data-intelligence.git data-intelligence
```

**Jika sudah pernah clone (update ke latest):**

```bash
cd /home/cdsw/data-intelligence
git pull origin main
```

Verifikasi:

```bash
ls /home/cdsw/data-intelligence/ask-data/
# Harus ada: backend/ frontend/ mcp_server/ qwen_inference/ data/ docs/ scripts/ sql/
```

---

### Step B — Download Model ke Cache Session

Download model **sebelum** deploy APP 1 supaya Application start tanpa menunggu download ulang.
Jalankan di **Workbench session** (bukan di dalam Application).

**1. Set token HuggingFace:**

```bash
export HUGGING_FACE_HUB_TOKEN=hf_xxxxxxxxxxxxxxxx
```

**2. (Opsional) Ganti model jika VRAM terbatas:**

```bash
# Hapus baris ini jika pakai model default (14B)
export QWEN_MODEL=Qwen/Qwen2.5-7B-Instruct-AWQ
```

**3. Jalankan script download:**

```bash
python3 /home/cdsw/data-intelligence/ask-data/qwen_inference/download_model.py
```

Output normal:

```text
INFO Model download: Qwen/Qwen2.5-14B-Instruct-AWQ
INFO Download complete. Local path: /home/cdsw/.cache/huggingface/hub/...
INFO Model ready. You can now deploy the Qwen LLM Application.
```

**4. Verifikasi:**

```bash
du -sh ~/.cache/huggingface/hub/models--Qwen--Qwen2.5-14B-Instruct-AWQ/
# Expected: ~8-9G
```

---

### Step C — Siapkan ChromaDB

File `chroma_db.zip` sudah ada di dalam repo dan berisi 17 chunks dari 5 dokumen PDF kebijakan.

**Extract dari repo:**

```bash
cd /home/cdsw/data-intelligence/ask-data
unzip chroma_db.zip
```

**Verifikasi:**

```bash
pip install pysqlite3-binary -q
python3 -c "
import sys, pysqlite3
sys.modules['sqlite3'] = pysqlite3
import chromadb
c = chromadb.PersistentClient('/home/cdsw/data-intelligence/ask-data/chroma_db')
col = c.get_collection('bankjatim_docs')
print('Chunks:', col.count())
"
# Expected: Chunks: 17
```

> Nama collection default adalah `bankjatim_docs`. Bisa diganti via env var `CHROMA_COLLECTION` di APP 2 & 3, asalkan nama yang sama konsisten.

---

### Step D — Pre-install vLLM Dependencies (Wajib Sebelum APP 1)

Jalankan di terminal **Workbench session** — bukan dari dalam Application.
Install di dalam Application OOM (exit 137) karena RAM runtime terbatas.

```bash
PIP_USER=0 pip install --target /home/cdsw/.vllm_deps \
  vllm==0.7.3 \
  torch==2.5.1 \
  "transformers==4.51.3" \
  "tokenizers>=0.19.0,<0.22" \
  accelerate \
  huggingface_hub \
  -q
```

> Proses ini membutuhkan **10–20 menit**. Tunggu sampai selesai sebelum deploy APP 1.

**Verifikasi:**

```bash
python3 -c "
import sys
sys.path.insert(0, '/home/cdsw/.vllm_deps')
import vllm, transformers
print('vLLM:', vllm.__version__)
print('transformers:', transformers.__version__)
"
# Expected: vLLM: 0.7.3 / transformers: 4.51.3
```

---

## APP 1 — Qwen LLM Application

**Tujuan:** Serve model Qwen via vLLM sebagai OpenAI-compatible inference server.
**Deploy ini PERTAMA** — Backend dan MCP Server memerlukan URL-nya.

---

### Step 1.1 — Buat Application Baru

Login ke CAI Workbench → pilih project → menu kiri **Applications** → **New Application**

---

### Step 1.2 — Isi Form Application

| Field | Nilai |
|---|---|
| **Name** | `<prefix>-ask-data-qwen` _(ganti `<prefix>` dengan identitas project)_ |
| **Subdomain** | _(auto-fill dari Name)_ |
| **Description** | `Qwen LLM inference server via vLLM — OpenAI-compatible API` |
| **Script** | `data-intelligence/ask-data/qwen_inference/qwen_entry.py` |
| **Engine Kernel** | `Python 3.10` |
| **Edition** | `Standard` |
| **Enable GPU** | ☑ On |
| **Number & Type of GPUs** | `1` (pilih GPU yang tersedia di resource group, minimal 22 GB VRAM) |
| **vCPU / Memory** | `4 vCPU / 16 GiB RAM` _(minimum)_ |

Centang: **☑ Allow Unauthenticated Access**

> Jika GPU yang tersedia berbeda (A10, A100, V100), sesuaikan `QWEN_GPU_MEMORY_UTILIZATION` berdasarkan total VRAM GPU tersebut.
> 2x GPU (tensor_parallel=2) tidak disarankan — CAI membatasi `/dev/shm` sehingga NCCL gagal.

---

### Step 1.3 — Set Environment Variables APP 1

| Key | Nilai | Keterangan |
|---|---|---|
| `QWEN_MODEL` | `Qwen/Qwen2.5-14B-Instruct-AWQ` | **Sesuaikan** dengan model yang didownload di Step B |
| `QWEN_API_KEY` | `<secret-token>` | **Sesuaikan** — harus sama dengan APP 2 & 3 |
| `QWEN_MAX_MODEL_LEN` | `4096` | Max context window — turunkan jika VRAM kurang |
| `QWEN_GPU_MEMORY_UTILIZATION` | `0.90` | 90% VRAM — turunkan ke `0.80` jika OOM |
| `QWEN_TENSOR_PARALLEL_SIZE` | `1` | Jumlah GPU — jangan ubah ke 2 di CAI |
| `VLLM_USE_FLASHINFER_SAMPLER` | `0` | Disable JIT compile flashinfer — nvcc tidak tersedia di CAI |

---

### Step 1.4 — Deploy dan Verifikasi

Klik **Create Application**. Tunggu status `Running` (3–5 menit jika model sudah ter-cache).

Pantau di tab **Logs** — startup sukses:

```text
INFO vLLM in deps: 0.7.3 — OK
INFO transformers in deps: 4.51.3 — OK
INFO Application startup complete.
```

Setelah Running, catat URL Application, lalu verifikasi dari terminal Workbench session:

```bash
QWEN_URL="https://<subdomain-app1>.<domain-cai-kamu>"

curl $QWEN_URL/v1/models -H "Authorization: Bearer <secret-token>"
# Expected: {"object":"list","data":[{"id":"Qwen/Qwen2.5-14B-Instruct-AWQ",...}]}

curl -X POST $QWEN_URL/v1/chat/completions \
  -H "Authorization: Bearer <secret-token>" \
  -H "Content-Type: application/json" \
  -d '{"model":"Qwen/Qwen2.5-14B-Instruct-AWQ","messages":[{"role":"user","content":"Halo"}],"max_tokens":30}'
# Expected: response JSON dengan content dari Qwen
```

> **Simpan URL ini** — akan dipakai sebagai `QWEN_BASE_URL` dan `OLLAMA_BASE_URL` di APP 2 & 3.

---

## APP 2 — Backend Application

**Tujuan:** FastAPI server — NL-to-SQL, Impala query, ChromaDB RAG, session management, table lock.
**Deploy setelah APP 1 Running.**

---

### Step 2.1 — Buat Application Baru

Menu kiri → **Applications** → **New Application**

---

### Step 2.2 — Isi Form Application

| Field | Nilai |
|---|---|
| **Name** | `<prefix>-ask-data-backend` |
| **Subdomain** | _(auto-fill)_ |
| **Description** | `FastAPI backend — NL-to-SQL, Impala CDW, ChromaDB RAG` |
| **Script** | `data-intelligence/ask-data/backend/backend_entry.py` |
| **Engine Kernel** | `Python 3.11` |
| **vCPU / Memory** | `4 vCPU / 8 GiB RAM` |
| **GPU** | Tidak diperlukan |
| **Replicas** | `1` |

Centang: **☑ Enable Unauthenticated Access**

---

### Step 2.3 — Set Environment Variables APP 2

**Wajib diisi (tidak ada default yang benar):**

| Key | Nilai | Keterangan |
|---|---|---|
| `QWEN_BASE_URL` | `https://<url-app1>/v1` | URL APP 1 + `/v1` di akhir |
| `QWEN_API_KEY` | `<secret-token>` | Sama dengan APP 1 |
| `QWEN_MODEL` | `Qwen/Qwen2.5-14B-Instruct-AWQ` | Sama dengan APP 1 |
| `IMPALA_HOST` | `<impala-host>` | Hostname Impala Virtual Warehouse |
| `IMPALA_PORT` | `443` | |
| `IMPALA_HTTP_PATH` | `cliservice` | |
| `CDP_USER` | `<cdp-username>` | |
| `CDP_PASS` | `<cdp-password>` | |
| `DB_NAME` | `<nama-database>` | Database yang berisi tabel target |
| `CHROMA_PERSIST_DIR` | `/home/cdsw/data-intelligence/ask-data/chroma_db` | **Absolute path** hasil unzip Step C — sesuaikan jika repo di-clone ke lokasi lain |
| `OLLAMA_BASE_URL` | `https://<url-app1>` | URL APP 1 **tanpa** `/v1` — untuk embedding |

**Opsional (ada default — ubah jika perlu):**

| Key | Default | Keterangan |
|---|---|---|
| `LLM_PROVIDER` | `local_qwen` | Provider aktif — jangan ubah kecuali punya Bedrock/Azure |
| `SESSION_BACKEND` | `sqlite` | `sqlite` atau `memory` |
| `SESSION_SQLITE_PATH` | `data/ask_data_sessions.db` | Path file SQLite relatif dari backend dir |
| `SESSION_TTL_MINUTES` | `30` | Durasi sesi sebelum expired |
| `MEMORY_MAX_HISTORY` | `10` | Max pesan history per sesi |
| `SQL_DEFAULT_LIMIT` | `100` | Default LIMIT pada query tanpa LIMIT eksplisit |
| `SQL_ALLOWED_TABLES` | `customer_dormant_segment` | Whitelist tabel — pisahkan koma jika lebih dari satu |
| `CHROMA_ENABLED` | `false` | Set `true` untuk aktifkan RAG (Knowledge Base) |
| `CHROMA_COLLECTION` | `bankjatim_docs` | **Sesuaikan** dengan nama collection yang diingest |
| `EMBED_MODEL` | `nomic-embed-text` | Embedding model via Ollama compat |
| `GUARDRAILS_ENABLED` | `false` | Set `true` untuk aktifkan PII blocking heuristic |
| `CORS_ALLOW_ORIGINS` | `*` | Batasi ke domain Frontend jika perlu |

> **Penting:**
> - `QWEN_BASE_URL` wajib ada `/v1` di akhir
> - `OLLAMA_BASE_URL` **tanpa** `/v1`
> - `CHROMA_PERSIST_DIR` harus absolute path ke folder hasil unzip Step C

---

### Step 2.4 — Deploy dan Verifikasi

Klik **Create Application**. Tunggu status `Running` (1–3 menit).

```bash
BACKEND_URL="https://<subdomain-app2>.<domain-cai-kamu>"

curl $BACKEND_URL/health
# Expected: {"status":"ok","session_backend":"sqlite","llm_providers":["local_qwen"],...}

curl $BACKEND_URL/health/db
# Expected: {"status":"ok","database":"<nama-database>","result":1}

curl $BACKEND_URL/rag/options
# Expected: {"enabled":true,"collections":[{"name":"bankjatim_docs","document_count":17}]}

curl $BACKEND_URL/tables
# Expected: {"status":"ok","tables":["customer_dormant_segment"],...}
```

> **Simpan URL ini** — akan dipakai sebagai `BACKEND_API_BASE_URL` di APP 4.

---

## APP 3 — MCP Server Application

**Tujuan:** Analytics tools terstruktur via HTTP — sql_query, dormant risk summary, campaign recommendation, RAG search.
**Deploy setelah APP 1 Running.**

---

### Step 3.1 — Buat Application Baru

Menu kiri → **Applications** → **New Application**

---

### Step 3.2 — Isi Form Application

| Field | Nilai |
|---|---|
| **Name** | `<prefix>-ask-data-mcp` |
| **Subdomain** | _(auto-fill)_ |
| **Description** | `MCP Server — structured analytics tools for dormant customer data` |
| **Script** | `data-intelligence/ask-data/mcp_server/mcp_entry.py` |
| **Engine Kernel** | `Python 3.11` |
| **vCPU / Memory** | `2 vCPU / 4 GiB RAM` |
| **GPU** | Tidak diperlukan |
| **Replicas** | `1` |

Centang: **☑ Enable Unauthenticated Access**

---

### Step 3.3 — Set Environment Variables APP 3

**Wajib diisi:**

| Key | Nilai | Keterangan |
|---|---|---|
| `IMPALA_HOST` | `<impala-host>` | Sama dengan APP 2 |
| `IMPALA_PORT` | `443` | |
| `IMPALA_HTTP_PATH` | `cliservice` | |
| `CDP_USER` | `<cdp-username>` | |
| `CDP_PASS` | `<cdp-password>` | |
| `DB_NAME` | `<nama-database>` | Sama dengan APP 2 |
| `CHROMA_PERSIST_DIR` | `/home/cdsw/data-intelligence/ask-data/chroma_db` | **Harus sama absolute path** dengan APP 2 |
| `OLLAMA_BASE_URL` | `https://<url-app1>` | URL APP 1 tanpa `/v1` |

**Opsional:**

| Key | Default | Keterangan |
|---|---|---|
| `CHROMA_COLLECTION` | `bankjatim_docs` | Sama dengan APP 2 |
| `EMBED_MODEL` | `nomic-embed-text` | Sama dengan APP 2 |

---

### Step 3.4 — Deploy dan Verifikasi

Klik **Create Application**. Tunggu status `Running` (1–2 menit).

```bash
MCP_URL="https://<subdomain-app3>.<domain-cai-kamu>"

curl $MCP_URL/health
# Expected: {"status":"ok","service":"mcp-server"}

curl $MCP_URL/tools | python3 -m json.tool
# Expected: 6 tools — sql_query, dormant_risk_summary, dormant_reason_breakdown,
#           campaign_recommendation, campaign_summary_by_reason, rag_search

curl -X POST $MCP_URL/tools/sql_query \
  -H "Content-Type: application/json" \
  -d "{\"sql\":\"SELECT COUNT(*) as total FROM <nama-database>.customer_dormant_segment\"}"
# Expected: {"tool":"sql_query","result":{"rows":[{"total":...}]}}
```

---

## APP 4 — Frontend Application

**Tujuan:** Next.js UI — chat interface, visualisasi chart, Settings panel (model, RAG, table lock).
**Deploy ini TERAKHIR** setelah URL APP 2 diketahui.

---

### Step 4.1 — Buat Application Baru

Menu kiri → **Applications** → **New Application**

---

### Step 4.2 — Isi Form Application

| Field | Nilai |
|---|---|
| **Name** | `<prefix>-ask-data-frontend` |
| **Subdomain** | _(auto-fill)_ |
| **Description** | `Next.js frontend — Ask Data UI` |
| **Script** | `data-intelligence/ask-data/frontend/frontend_entry.py` |
| **Engine Kernel** | `Python 3.11` |
| **vCPU / Memory** | `2 vCPU / 4 GiB RAM` |
| **GPU** | Tidak diperlukan |
| **Replicas** | `1` |

Centang: **☑ Enable Unauthenticated Access**

---

### Step 4.3 — Set Environment Variables APP 4

| Key | Nilai | Keterangan |
|---|---|---|
| `BACKEND_API_BASE_URL` | `https://<subdomain-app2>.<domain-cai-kamu>` | URL APP 2 — **tanpa** trailing slash |

> Ini satu-satunya env var yang dibutuhkan di APP 4.
> Semua config LLM, Impala, dan RAG dikonfigurasi di APP 2 (Backend).

---

### Step 4.4 — Deploy dan Verifikasi

Klik **Create Application**. Tunggu status `Running`.

Pertama kali: **3–7 menit** (`npm install` + `npm build` berjalan otomatis).
Startup sukses ditandai di Logs:

```text
info  - Ready in Xs
```

Buka URL Frontend di browser:

**Test 1 — UI terbuka:** Welcome screen muncul, toggle EN/ID berfungsi.

**Test 2 — SQL query:** Ketik *"Tampilkan jumlah nasabah per segmen"* → tunggu 5–15 detik → jawaban + bar chart muncul.

**Test 3 — Settings panel:** Klik ikon Settings → dropdown table lock bisa dipilih → RAG section bisa dikonfigurasi dan disimpan.

**Test 4 — Guardrails:** Ketik *"tampilkan nomor hp semua nasabah"* → respons diblok dengan pesan PII protection.

---

## Environment Variable Reference — Lengkap

Tabel ini adalah referensi semua env var yang bisa dikonfigurasi ulang saat deploy di environment berbeda.

### APP 1 — Qwen LLM

| Key | Default | Wajib | Keterangan |
|---|---|---|---|
| `QWEN_MODEL` | `Qwen/Qwen2.5-14B-Instruct-AWQ` | Ya | HuggingFace model ID — sesuaikan dengan model yang didownload |
| `QWEN_API_KEY` | `local-dev-token` | Ya | Token autentikasi internal — harus sama di APP 1, 2, 3 |
| `QWEN_MAX_MODEL_LEN` | `4096` | Tidak | Max context tokens — turunkan jika VRAM kurang |
| `QWEN_GPU_MEMORY_UTILIZATION` | `0.90` | Tidak | Fraksi VRAM yang dipakai — turunkan ke `0.80` jika OOM |
| `QWEN_TENSOR_PARALLEL_SIZE` | `1` | Tidak | Jumlah GPU — jangan ubah ke 2 di CAI |
| `VLLM_USE_FLASHINFER_SAMPLER` | `0` | Tidak | Disable JIT compile flashinfer |
| `HUGGING_FACE_HUB_TOKEN` | _(kosong)_ | Tidak* | *Tidak dibutuhkan jika model sudah ter-cache |

### APP 2 — Backend

| Key | Default | Wajib | Keterangan |
|---|---|---|---|
| `QWEN_BASE_URL` | `http://localhost:8000/v1` | **Ya** | URL APP 1 + `/v1` |
| `QWEN_API_KEY` | `local-dev-token` | **Ya** | Sama dengan APP 1 |
| `QWEN_MODEL` | `Qwen/Qwen3-8B-AWQ` | **Ya** | Sama dengan APP 1 |
| `IMPALA_HOST` | _(kosong)_ | **Ya** | Hostname Impala |
| `IMPALA_PORT` | `443` | **Ya** | |
| `IMPALA_HTTP_PATH` | _(kosong)_ | **Ya** | |
| `CDP_USER` | _(kosong)_ | **Ya** | |
| `CDP_PASS` | _(kosong)_ | **Ya** | |
| `DB_NAME` | `cai_sdx_se_indonesia` | **Ya** | Nama database — **sesuaikan** |
| `CHROMA_PERSIST_DIR` | `./chroma_db` | **Ya** | Absolute path ke ChromaDB — **sesuaikan** |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | **Ya** | URL APP 1 tanpa `/v1` |
| `LLM_PROVIDER` | `local_qwen` | Tidak | Provider aktif |
| `SESSION_BACKEND` | `sqlite` | Tidak | `sqlite` atau `memory` |
| `SESSION_SQLITE_PATH` | `data/ask_data_sessions.db` | Tidak | Path file SQLite |
| `SESSION_TTL_MINUTES` | `30` | Tidak | Durasi sesi (menit) |
| `MEMORY_MAX_HISTORY` | `10` | Tidak | Max history pesan per sesi |
| `SQL_DEFAULT_LIMIT` | `100` | Tidak | Default LIMIT query |
| `SQL_ALLOWED_TABLES` | `customer_dormant_segment` | Tidak | Whitelist tabel, pisah koma |
| `CHROMA_ENABLED` | `false` | Tidak | `true` untuk aktifkan RAG |
| `CHROMA_COLLECTION` | `bankjatim_docs` | Tidak | Nama collection ChromaDB |
| `EMBED_MODEL` | `nomic-embed-text` | Tidak | Embedding model |
| `GUARDRAILS_ENABLED` | `false` | Tidak | `true` untuk aktifkan PII blocking |
| `CORS_ALLOW_ORIGINS` | `*` | Tidak | Domain yang diizinkan |

### APP 3 — MCP Server

| Key | Default | Wajib | Keterangan |
|---|---|---|---|
| `IMPALA_HOST` | _(kosong)_ | **Ya** | |
| `IMPALA_PORT` | `443` | **Ya** | |
| `IMPALA_HTTP_PATH` | _(kosong)_ | **Ya** | |
| `CDP_USER` | _(kosong)_ | **Ya** | |
| `CDP_PASS` | _(kosong)_ | **Ya** | |
| `DB_NAME` | `cai_sdx_se_indonesia` | **Ya** | **Sesuaikan** |
| `CHROMA_PERSIST_DIR` | `./chroma_db` | **Ya** | Absolute path, sama dengan APP 2 |
| `OLLAMA_BASE_URL` | _(kosong)_ | **Ya** | URL APP 1 tanpa `/v1` |
| `CHROMA_COLLECTION` | `bankjatim_docs` | Tidak | Sama dengan APP 2 |
| `EMBED_MODEL` | `nomic-embed-text` | Tidak | Sama dengan APP 2 |

### APP 4 — Frontend

| Key | Default | Wajib | Keterangan |
|---|---|---|---|
| `BACKEND_API_BASE_URL` | _(kosong)_ | **Ya** | URL APP 2 tanpa trailing slash |

---

## Troubleshooting

### APP 1 — Error `DEPS NOT READY`

Step D belum dijalankan, atau deps tidak valid. Jalankan ulang Step D dari terminal Workbench session, lalu restart Application.

### APP 1 — Error `CUDA out of memory`

Turunkan `QWEN_GPU_MEMORY_UTILIZATION` ke `0.80` atau `0.75`, atau ganti ke model yang lebih kecil (lihat Step 0.4).

### APP 1 — Error `undefined symbol: ncclCommWindowDeregister`

Versi torch tidak kompatibel dengan NCCL di CAI. Pastikan Step D menginstall `torch==2.5.1` (bukan versi lebih baru). Jalankan ulang Step D jika perlu.

### APP 1 — Error `Could not find nvcc` / flashinfer gagal

Pastikan `VLLM_USE_FLASHINFER_SAMPLER=0` sudah diset di env vars Application.

### APP 1 — Model tidak ditemukan saat startup

Model belum ter-cache. Jalankan ulang Step B, atau set `HUGGING_FACE_HUB_TOKEN` di env var Application agar download saat startup (akan lambat ~15–30 menit).

### APP 1 — Error `Qwen2Tokenizer has no attribute all_special_tokens_extended`

Versi transformers tidak kompatibel (5.x terinstall, butuh 4.51.x). Jalankan ulang Step D dengan versi yang benar, lalu restart Application.

### APP 2 — `/health/db` return error

- `TSocket read 0 bytes` → `CDP_USER` / `CDP_PASS` salah, atau network CAI tidak bisa reach Impala host
- `Table not found` → `DB_NAME` salah, atau tabel belum ada di database target

Verifikasi koneksi Impala dari Workbench session:

```bash
python3 -c "
from impala.dbapi import connect
conn = connect(
  host='<impala-host>', port=443, use_ssl=True,
  auth_mechanism='PLAIN', user='<cdp-user>', password='<cdp-pass>'
)
cur = conn.cursor()
cur.execute('SELECT 1')
print('Impala OK:', cur.fetchone())
"
```

### APP 2 — `/rag/options` return `{"enabled":false}`

- `CHROMA_ENABLED=true` belum diset, atau
- `CHROMA_PERSIST_DIR` menunjuk ke folder yang kosong / belum di-unzip

### APP 2 — `/chat/query` timeout atau error 502

- Pastikan APP 1 sudah `Running`
- Pastikan `QWEN_BASE_URL` ada `/v1` di akhir

### APP 4 — Blank page / CORS error

- Pastikan `BACKEND_API_BASE_URL` tidak ada trailing slash
- Pastikan semua Application sudah centang **Enable Unauthenticated Access**
- Buka browser DevTools → Network → lihat request yang gagal

### APP 4 — Build gagal / lama

- Logs menampilkan `npm ERR!` → restart Application (npm install ulang otomatis)
- Build pertama kali bisa memakan 5–10 menit

---

## Checklist Final

### Persiapan

- [ ] Repo di-clone ke `/home/cdsw/data-intelligence/`
- [ ] Model ter-cache di `~/.cache/huggingface/hub/` (~8–9 GB)
- [ ] ChromaDB siap — `col.count()` = 17
- [ ] `/home/cdsw/.vllm_deps` berisi vLLM 0.7.3 + transformers 4.51.3

### APP 1 — Qwen LLM

- [ ] Script: `data-intelligence/ask-data/qwen_inference/qwen_entry.py`
- [ ] Resource: GPU aktif, ≥16 GiB RAM
- [ ] Env: `QWEN_MODEL`, `QWEN_API_KEY`, `QWEN_MAX_MODEL_LEN`, `QWEN_GPU_MEMORY_UTILIZATION`, `VLLM_USE_FLASHINFER_SAMPLER=0`
- [ ] Unauthenticated Access: ☑
- [ ] Status: **Running** — `curl <url>/v1/models` OK
- [ ] **URL dicatat**

### APP 2 — Backend

- [ ] Script: `data-intelligence/ask-data/backend/backend_entry.py`
- [ ] Resource: 4 vCPU / 8 GiB, no GPU
- [ ] Env wajib: `QWEN_BASE_URL` (+`/v1`), `QWEN_API_KEY`, `QWEN_MODEL`, semua `IMPALA_*` & `CDP_*`, `DB_NAME`, `CHROMA_PERSIST_DIR`, `OLLAMA_BASE_URL`
- [ ] Env opsional: `CHROMA_ENABLED=true`, `GUARDRAILS_ENABLED=true`
- [ ] Unauthenticated Access: ☑
- [ ] Status: **Running** — `/health`, `/health/db`, `/rag/options` semua OK
- [ ] **URL dicatat**

### APP 3 — MCP Server

- [ ] Script: `data-intelligence/ask-data/mcp_server/mcp_entry.py`
- [ ] Resource: 2 vCPU / 4 GiB, no GPU
- [ ] Env wajib: semua `IMPALA_*` & `CDP_*`, `DB_NAME`, `CHROMA_PERSIST_DIR`, `OLLAMA_BASE_URL`
- [ ] Unauthenticated Access: ☑
- [ ] Status: **Running** — `/health` OK, `/tools` return 6 tools

### APP 4 — Frontend

- [ ] Script: `data-intelligence/ask-data/frontend/frontend_entry.py`
- [ ] Resource: 2 vCPU / 4 GiB, no GPU
- [ ] Env: `BACKEND_API_BASE_URL` (tanpa trailing slash)
- [ ] Unauthenticated Access: ☑
- [ ] Status: **Running** — UI terbuka di browser
- [ ] SQL query → jawaban + chart ✓
- [ ] Settings panel → table lock & RAG config berfungsi ✓
- [ ] Guardrails → PII query diblok ✓
