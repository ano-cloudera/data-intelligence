# Ask Data — Project State (Bank Jawa Timur PoC)

_Last updated: 2026-05-14_

---

## 1. Executive Summary

**Customer:** Bank Jawa Timur (Bank Jatim)  
**Use Case:** AI-powered Customer Analytics Assistant — Natural Language to SQL + RAG Document Q&A  
**Status:** ✅ End-to-end working locally, siap demo

Asisten analitik berbahasa Indonesia yang memungkinkan tim bisnis mengajukan pertanyaan tentang data segmentasi nasabah dalam bahasa alami. Backend generate SQL, eksekusi ke Impala/CDW Cloudera, dan kembalikan jawaban dalam Bahasa Indonesia. Selain SQL, asisten juga bisa menjawab pertanyaan berbasis dokumen kebijakan via ChromaDB (RAG).

---

## 2. Demo Flow

### SQL Flow (default)
1. User buka frontend → AI Assistant
2. User tanya dalam Bahasa Indonesia (contoh: "Berapa jumlah nasabah per segmen?")
3. Frontend kirim ke `POST /chat/query`
4. Backend generate SQL via Qwen2.5:7b (Ollama), eksekusi ke Impala CDW
5. Backend kembalikan: jawaban Bahasa Indonesia + SQL + rows + visualization spec
6. Frontend render jawaban + chart (bar/line/pie/table) otomatis

### RAG Flow (Knowledge Base aktif)
1. User klik tombol **"Knowledge Base"** di topbar
2. User enable RAG, pilih collection `bankjatim_docs`, set top_k
3. Frontend save config via `POST /rag/config`
4. Pertanyaan selanjutnya dikirim ke `POST /chat/answer`
5. Backend query ChromaDB → ambil chunks relevan → kirim ke Qwen → jawaban dengan sumber PDF

---

## 3. Architecture

| Layer | Teknologi |
|---|---|
| Structured data | Impala / CDW (Cloudera Data Warehouse) |
| LLM provider | Qwen2.5:7b via Ollama (lokal M1 Mac) |
| Vector store | ChromaDB embedded (PersistentClient) |
| Embedding model | `nomic-embed-text` via Ollama |
| Backend | FastAPI + Uvicorn, Python 3.11 |
| Frontend | Next.js 15 + Tailwind CSS + TypeScript |
| Session store | SQLite |
| Deployment target | Cloudera AI Applications (CAI) |

### Catatan penting
- Untuk demo lokal: Ollama serve Qwen2.5:7b di `http://localhost:11434/v1`
- Untuk deploy ke CAI: ganti `LLM_PROVIDER=local_qwen` ke `vllm` atau provider lain yang di-support
- ChromaDB `persist_dir` perlu mount ke persistent storage saat di CAI

---

## 4. Data Model

**Database:** `cai_sdx_se_indonesia`  
**Table:** `customer_dormant_segment`  
**Rows:** 10.000 (synthetic, non-PII)  
**Storage:** Impala native PARQUET di S3 path `s3a://go01-demo/user/cai-demo-se-indonesia/data/customer dormant segmentation/`

**Kolom utama:** 47 kolom — customer profile, segment, dormant risk, deposito, kredit, campaign, cabang, digital activity.  
Detail lengkap: [customer_dormant_segment_metadata.md](customer_dormant_segment_metadata.md)

**Sample queries yang sudah diverifikasi:**
- `SELECT customer_segment, COUNT(*) FROM ... GROUP BY customer_segment` → 7 segmen
- Total saldo deposito per segmen
- Nasabah dormant risk HIGH
- Distribusi kota per segmen

---

## 5. Backend

**Entry point:** `backend/backend_entry.py`  
**Jalankan lokal:** `cd ask-data && .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8080`

### Key endpoints

| Endpoint | Purpose |
|---|---|
| `GET /health` | App liveness check |
| `GET /health/db` | Impala connectivity check |
| `GET /llm/providers` | List LLM providers yang tersedia |
| `POST /llm/providers/select` | Pilih LLM provider untuk session |
| `GET /rag/options` | List ChromaDB collections |
| `GET /rag/config/{session_id}` | Load RAG config session |
| `POST /rag/config` | Save RAG config session |
| `POST /rag/ingest` | Ingest PDF ke ChromaDB collection |
| `POST /chat/query` | SQL flow: NL → SQL → Impala → answer + visualization |
| `POST /chat/answer` | RAG flow: NL → ChromaDB → Qwen → answer + sources |
| `GET /sessions` | List recent sessions |
| `GET /sessions/{session_id}` | Load session history |
| `GET /analytics/summary` | Usage metrics ringkasan |
| `GET /analytics/events` | Recent activity log |

### LLM Provider: Qwen2.5:7b via Ollama
- `LLM_PROVIDER=local_qwen`
- `QWEN_BASE_URL=http://localhost:11434/v1`
- `QWEN_API_KEY=ollama`
- `QWEN_MODEL=qwen2.5:7b`
- Compatible dengan OpenAI Python SDK

### ChromaDB RAG
- `CHROMA_ENABLED=true`
- `CHROMA_PERSIST_DIR=./chroma_db`
- `EMBED_MODEL=nomic-embed-text`
- `OLLAMA_BASE_URL=http://localhost:11434`
- Collection: `bankjatim_docs` — 17 chunks dari 5 PDF
- Embedding: `OllamaEmbeddingFunction` (fallback ke SentenceTransformer)

### Impala Connection
- `IMPALA_HOST=coordinator-default-impala-aws.dw-go01-demo-aws.ylcu-atmi.cloudera.site`
- `IMPALA_PORT=443`
- `IMPALA_HTTP_PATH=cliservice`
- `CDP_USER=triano`
- `DB_NAME=cai_sdx_se_indonesia`

### Guardrails
- `GUARDRAILS_ENABLED=true`
- Mode: `local-only` (custom heuristic, tidak pakai guardrails-ai library)
- Block: PII requests (nomor hp, email nasabah, dll), prompt injection, out-of-scope
- Redact: email, phone, long numerics dari jawaban

### Visualization
- Backend generate visualization spec (type, title, x_key, y_key, series, table_rows)
- Supported: `bar`, `line`, `pie`, `table`
- Frontend render otomatis via Recharts

---

## 6. Frontend

**Stack:** Next.js 15 (App Router), Tailwind CSS 3, TypeScript, Recharts, @mui/icons-material  
**Jalankan lokal:** `cd ask-data/frontend && npm run dev` → http://localhost:3000

### Key components
| Component | Purpose |
|---|---|
| `app/page.tsx` | Main page — chat state, RAG state, session management |
| `lib/api.ts` | Typed API client → proxy `/api/backend` |
| `components/rag-config-modal.tsx` | ChromaDB RAG config modal (collection picker + top_k) |
| `components/answer-card.tsx` | Render jawaban asisten + RAG sources |
| `components/result-chart-card.tsx` | Render visualization spec (chart/table) |
| `components/model-settings-panel.tsx` | Provider selector (termasuk `local_qwen`) |
| `components/chat-input-panel.tsx` | Input area + starter prompts |

### RAG UI (ChromaDB)
- Tombol **"Knowledge Base"** di topbar (bukan "RAG Studio")
- Modal: enable/disable toggle, collection dropdown, top_k slider (1–10)
- `VectorRagConfig { enabled, collection_name, top_k }` — sudah aligned dengan backend schema
- Status aktif: badge hijau "Knowledge Base Aktif"

### Starter prompts (Bank Jatim)
1. "Tampilkan jumlah nasabah berdasarkan customer segment."
2. "Segmen mana yang memiliki risiko dormant paling tinggi?"
3. "Berapa total saldo deposito untuk nasabah dormant risk high?"

### API routing
- Frontend proxy: `/api/backend` → `BACKEND_API_BASE_URL`
- SQL chat: `POST /chat/query`
- RAG chat: `POST /chat/answer` (saat `enabled && collection_name`)
- RAG config: `GET /rag/config/{session_id}`, `POST /rag/config`
- RAG options: `GET /rag/options`

---

## 7. RAG Documents (ChromaDB)

Collection: `bankjatim_docs` — 17 chunks  

| File | Konten |
|---|---|
| `01_strategi_customer_segmentation_portfolio_bank_jatim.pdf` | Segmentasi portfolio nasabah |
| `02_dormant_customer_retention_strategy_bank_jatim.pdf` | Strategi retensi nasabah dormant |
| `03_campaign_planning_next_best_action_bank_jatim.pdf` | Campaign planning & NBA |
| `04_branch_city_segment_channel_analytics_playbook.pdf` | Analytics cabang & kota |
| `05_customer_analytics_governance_decisioning_policy.pdf` | Kebijakan governance analytics |

**Ingest script:** `scripts/ingest_documents.py`  
```bash
cd ask-data && PYTHONPATH=backend .venv/bin/python scripts/ingest_documents.py
```

---

## 8. Environment Variables Lengkap

File: `ask-data/.env` (jangan commit ke git — sudah ada di `.gitignore`)

```env
LLM_PROVIDER=local_qwen
QWEN_BASE_URL=http://localhost:11434/v1
QWEN_API_KEY=ollama
QWEN_MODEL=qwen2.5:7b

IMPALA_HOST=coordinator-default-impala-aws.dw-go01-demo-aws.ylcu-atmi.cloudera.site
IMPALA_PORT=443
IMPALA_HTTP_PATH=cliservice
CDP_USER=triano
CDP_PASS=<redacted>
DB_NAME=cai_sdx_se_indonesia

SESSION_BACKEND=sqlite
GUARDRAILS_ENABLED=true

CHROMA_ENABLED=true
CHROMA_PERSIST_DIR=./chroma_db
EMBED_MODEL=nomic-embed-text
OLLAMA_BASE_URL=http://localhost:11434
```

---

## 9. Progress Checklist

### ✅ Selesai

#### Data & Infrastructure
- [x] Design table `customer_dormant_segment` — 47 kolom, 10.000 rows synthetic
- [x] DDL Impala native PARQUET (bukan Iceberg) di `sql/impala_customer_dormant_segment_ddl.sql`
- [x] Data upload ke Impala CDW via Hue — verified 10.000 rows
- [x] Koneksi Impala dari backend verified (`COUNT(*)` = 10.000)
- [x] Database rename: `bankjatim` → `cai_sdx_se_indonesia`
- [x] Table rename: `customer_ai_profile` → `customer_dormant_segment`
- [x] Schema metadata & business glossary: `docs/customer_dormant_segment_metadata.md`

#### LLM Setup
- [x] Ollama install di M1 Mac + pull `qwen2.5:7b`
- [x] Pull embedding model `nomic-embed-text`
- [x] Python venv `.venv` dengan Python 3.11 + semua dependencies installed
- [x] `LLM_PROVIDER=local_qwen` routing di backend

#### Backend
- [x] FastAPI backend berjalan di port 8080
- [x] SQL flow end-to-end: NL → Qwen → SQL → Impala → jawaban Bahasa Indonesia ✅
- [x] Visualization spec generation (bar/line/pie/table)
- [x] ChromaDB integration — `ChromaRagClient` di `services/rag_client.py`
- [x] RAG flow end-to-end: NL → ChromaDB → Qwen → jawaban + sumber PDF ✅
- [x] 5 PDF diingest ke collection `bankjatim_docs` (17 chunks)
- [x] Guardrails local mode (custom heuristic)
- [x] Session management (SQLite)
- [x] Analytics events logging
- [x] `POST /rag/ingest` endpoint untuk ingest PDF via API
- [x] `GET /rag/options` mengembalikan daftar ChromaDB collections
- [x] Schema telah di-cleanup dari sisa referensi RAG Studio lama

#### Frontend
- [x] UI berbahasa Indonesia, bertema Bank Jawa Timur
- [x] Starter prompts relevan ke use case dormant nasabah
- [x] `rag-config-modal.tsx` ditulis ulang — collection picker + top_k (bukan RAG Studio fields)
- [x] `model-settings-panel.tsx` ditambah case `local_qwen`
- [x] `lib/api.ts` — RAG types diganti ke `VectorRagConfig`, `RagCollectionOption`, `RagOptionsResponse`
- [x] `page.tsx` — semua logika RAG Studio lama diganti ke ChromaDB flow
- [x] TypeScript compile: 0 errors
- [x] Endpoint test via curl: semua ✅

---

### ❌ Belum Selesai / Next Steps

#### MCP Server
- [ ] MCP Server sebagai CAI Application terpisah — tool-based structured queries
- [ ] Tools yang direncanakan: `query_customer_segment`, `get_dormant_risk_summary`, `get_campaign_recommendation`

#### CAI Deployment
- [ ] Deploy Backend sebagai CAI Application
  - [ ] Ganti `LLM_PROVIDER` ke provider yang tersedia di CAI (vLLM atau Bedrock)
  - [ ] Set env vars di CAI (Impala creds, LLM config)
  - [ ] Pastikan ChromaDB `persist_dir` ke persistent storage
  - [ ] Upload `chroma_db/` atau re-ingest PDF setelah deploy
- [ ] Deploy Frontend sebagai CAI Application
  - [ ] Set `BACKEND_API_BASE_URL` ke URL backend CAI Application
- [ ] Deploy Qwen/vLLM sebagai CAI Application (GPU) — untuk produksi bukan Ollama
- [ ] Smoke test end-to-end di CAI environment

#### Testing & Polish
- [ ] Test live di browser (http://localhost:3000) — RAG modal flow, SQL chat, visualization
- [ ] Unit test update untuk schema baru (beberapa test masih referensi schema lama)
- [ ] Guardrails test untuk Bahasa Indonesia PII patterns

#### Optional / Future
- [ ] RAG ingest UI — upload PDF langsung dari frontend (saat ini via API/script)
- [ ] Conversation memory improvements — ringkasan konteks multi-turn
- [ ] Multi-table support (jika ada tabel lain di `cai_sdx_se_indonesia`)

---

## 10. Resume Instructions

Saat mulai session baru, assume:
1. Use case: Customer Analytics + Dormant Risk, Bank Jawa Timur
2. Data: `cai_sdx_se_indonesia.customer_dormant_segment`, 10.000 rows di Impala CDW
3. LLM: Qwen2.5:7b via Ollama lokal M1 Mac (`http://localhost:11434/v1`)
4. RAG: ChromaDB embedded di `./chroma_db`, collection `bankjatim_docs`, 17 chunks
5. Backend: FastAPI port 8080 — cek `lsof -i :8080` apakah sudah running
6. Frontend: Next.js port 3000 — cek `lsof -i :3000` apakah sudah running
7. Semua flow sudah verified working — fokus ke CAI deployment atau feature tambahan
8. `.env` ada di `ask-data/.env` — jangan di-commit

---

End of project state.
