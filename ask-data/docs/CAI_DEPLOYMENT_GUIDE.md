# CAI Deployment Guide — Bank Jawa Timur PoC

> Deploy 4 Cloudera AI Applications dalam urutan berikut:
> **Qwen LLM → Backend → MCP Server → Frontend**

---

## Persiapan Awal (Lakukan Sekali)

### 1. Sync project ke CAI Workbench Session

Jalankan di terminal CAI Workbench session:

```bash
python sync_project.py
```

Pastikan folder `bank-jawa-timur/ask-data/` sudah tersedia setelah sync.

### 2. Upload ChromaDB ke Workbench Session

ChromaDB tidak di-commit ke git. Upload folder `chroma_db/` dari Mac lokal ke CAI:

**Option A — via CAI File Upload UI:**
Upload seluruh folder `chroma_db/` ke root project di Workbench session.
Target path: `/home/cdsw/bank-jawa-timur/ask-data/chroma_db/`

**Option B — re-ingest dari PDF (jika PDF sudah ada di session):**
```bash
cd bank-jawa-timur/ask-data
pip install -r backend/requirements.txt
PYTHONPATH=backend python scripts/ingest_documents.py
```

> PDF harus ada di `ask-data/data/documents/` terlebih dahulu.

---

## APP 1 — Qwen LLM Application

> Serve Qwen2.5-14B-Instruct-AWQ via vLLM. **Deploy ini pertama** karena Backend dan MCP butuh URL-nya.

### Settings di CAI

| Field | Value |
|---|---|
| **Name** | `bank-jatim-qwen-llm` |
| **Script** | `bank-jawa-timur/ask-data/qwen_inference/qwen_entry.py` |
| **Engine** | Python 3.11 |
| **Resource Profile** | GPU — pilih profile dengan **1x L40 (48 GB VRAM)** |
| **Replicas** | 1 |

### Environment Variables

| Key | Value |
|---|---|
| `QWEN_MODEL` | `Qwen/Qwen2.5-14B-Instruct-AWQ` |
| `QWEN_API_KEY` | `local-dev-token` |
| `QWEN_MAX_MODEL_LEN` | `8192` |
| `QWEN_GPU_MEMORY_UTILIZATION` | `0.90` |
| `QWEN_TENSOR_PARALLEL_SIZE` | `1` |
| `HUGGING_FACE_HUB_TOKEN` | `<hf-token>` _(jika model perlu download)_ |

### Verification

Setelah Application running, buka URL Application-nya dan test:

```bash
curl https://<qwen-app-url>/health
# Expected: {"status":"ok","provider":"local_qwen",...}

curl -X POST https://<qwen-app-url>/v1/chat/completions \
  -H "Authorization: Bearer local-dev-token" \
  -H "Content-Type: application/json" \
  -d '{"model":"Qwen/Qwen2.5-14B-Instruct-AWQ","messages":[{"role":"user","content":"Halo"}],"max_tokens":50}'
```

> **Catat URL Qwen App** — akan dipakai sebagai `QWEN_BASE_URL` di Backend dan MCP.

---

## APP 2 — Backend Application

> FastAPI server — SQL generation, Impala, ChromaDB RAG, session management.

### Settings di CAI

| Field | Value |
|---|---|
| **Name** | `bank-jatim-backend` |
| **Script** | `bank-jawa-timur/ask-data/backend/backend_entry.py` |
| **Engine** | Python 3.11 |
| **Resource Profile** | CPU — 4 vCPU, 8 GB RAM |
| **Replicas** | 1 |

### Environment Variables

| Key | Value |
|---|---|
| `LLM_PROVIDER` | `local_qwen` |
| `QWEN_BASE_URL` | `https://<qwen-app-url>/v1` |
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
| `OLLAMA_BASE_URL` | `https://<qwen-app-url>` |

> **Catatan `CHROMA_PERSIST_DIR`:** Gunakan absolute path ke folder chroma_db di Workbench session, bukan relative path. Pastikan folder sudah ada sebelum deploy.

### Verification

```bash
curl https://<backend-app-url>/health
# Expected: {"status":"ok","session_backend":"sqlite","llm_provider":"local_qwen",...}

curl https://<backend-app-url>/health/db
# Expected: {"status":"ok","database":"cai_sdx_se_indonesia","result":1}

curl https://<backend-app-url>/rag/options
# Expected: {"enabled":true,"collections":[{"name":"bankjatim_docs","document_count":17}]}
```

> **Catat URL Backend App** — akan dipakai sebagai `BACKEND_API_BASE_URL` di Frontend.

---

## APP 3 — MCP Server Application

> Structured analytics tools — sql_query, dormant risk, campaign, RAG search.

### Settings di CAI

| Field | Value |
|---|---|
| **Name** | `bank-jatim-mcp-server` |
| **Script** | `bank-jawa-timur/ask-data/mcp_server/mcp_entry.py` |
| **Engine** | Python 3.11 |
| **Resource Profile** | CPU — 2 vCPU, 4 GB RAM |
| **Replicas** | 1 |

### Environment Variables

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
| `OLLAMA_BASE_URL` | `https://<qwen-app-url>` |

### Verification

```bash
curl https://<mcp-app-url>/health
# Expected: {"status":"ok","service":"mcp-server"}

curl https://<mcp-app-url>/tools
# Expected: list of 6 tools

# Quick tool test:
curl -X POST https://<mcp-app-url>/tools/dormant_risk_summary \
  -H "Content-Type: application/json" \
  -d '{"risk_level":"HIGH"}'
```

---

## APP 4 — Frontend Application

> Next.js UI — chat interface, visualization, RAG config modal. **Deploy ini terakhir.**

### Settings di CAI

| Field | Value |
|---|---|
| **Name** | `bank-jatim-frontend` |
| **Script** | `bank-jawa-timur/ask-data/frontend/frontend_entry.py` |
| **Engine** | Python 3.11 _(launcher script only, Node.js dijalankan dari dalam)_ |
| **Resource Profile** | CPU — 2 vCPU, 4 GB RAM |
| **Replicas** | 1 |

### Environment Variables

| Key | Value |
|---|---|
| `BACKEND_API_BASE_URL` | `https://<backend-app-url>` |

### Verification

Buka URL Frontend Application di browser:
- Welcome screen muncul dengan logo Cloudera dan greeting Bahasa Indonesia ✅
- Klik **"Knowledge Base"** di topbar → modal terbuka, collection `bankjatim_docs` muncul ✅
- Ketik pertanyaan: `"Berapa jumlah nasabah per segmen?"` → jawaban + bar chart muncul ✅
- Enable RAG, simpan config → tanya `"Apa strategi retensi nasabah dormant?"` → jawaban dengan sumber PDF ✅

---

## Troubleshooting

### Qwen LLM tidak mau start
- Pastikan resource profile punya GPU L40
- Cek log untuk error download model dari HuggingFace — set `HUGGING_FACE_HUB_TOKEN`
- Jika VRAM tidak cukup, turunkan `QWEN_MAX_MODEL_LEN` ke `4096`

### Backend: `CHROMA_ENABLED=true` tapi RAG tidak jalan
- Pastikan `CHROMA_PERSIST_DIR` adalah **absolute path** dan folder `chroma_db` sudah ada di sana
- Jalankan `ingest_documents.py` di Workbench session jika chroma_db kosong

### Backend: Impala connection error
- Pastikan CAI environment bisa reach Impala host (network/VPN)
- Cek `CDP_USER` dan `CDP_PASS` benar
- Test dari Workbench session: `python -c "from impala.dbapi import connect; c=connect(host='...',port=443,use_ssl=True,auth_mechanism='PLAIN',use_http_transport=True,http_path='cliservice',user='triano',password='...')"`

### Frontend: blank page atau 502
- Pastikan `BACKEND_API_BASE_URL` tidak ada trailing slash
- Pastikan **"Allow Unauthenticated Access"** diaktifkan di **semua** 4 Applications
- Cek `next.config.ts` — proxy rewrite `/api/backend` harus match URL backend

### Model response sangat lambat
- Qwen2.5-14B-AWQ di L40 normal ~3–8 detik per response
- Jika timeout, naikkan timeout di backend settings atau gunakan `QWEN_MAX_MODEL_LEN=4096`

---

## Dependency Map

```
Frontend App
    │  BACKEND_API_BASE_URL
    ▼
Backend App ──── IMPALA_HOST ────► Impala CDW
    │  QWEN_BASE_URL              (cai_sdx_se_indonesia)
    ▼
Qwen LLM App
(vLLM, GPU L40)

MCP Server App ── IMPALA_HOST ───► Impala CDW
    │  OLLAMA_BASE_URL
    ▼
Qwen LLM App (embedding only, via OLLAMA_BASE_URL)
```

---

## Checklist Deploy

- [ ] `sync_project.py` dijalankan di Workbench session → code tersedia
- [ ] `chroma_db/` folder diupload atau di-ingest ulang di session
- [ ] **APP 1** Qwen LLM running → URL dicatat
- [ ] **APP 2** Backend running → health ✅, db ✅, rag/options ✅ → URL dicatat
- [ ] **APP 3** MCP Server running → health ✅, tools ✅
- [ ] **APP 4** Frontend running → chat SQL ✅, RAG ✅, chart ✅
- [ ] Semua Applications: **"Allow Unauthenticated Access"** = ON
