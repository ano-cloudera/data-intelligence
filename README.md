# Bank Jawa Timur — AI Analytics PoC

Cloudera AI demo workspace untuk Bank Jawa Timur.
AI-powered customer analytics assistant: NL-to-SQL, ChromaDB RAG, MCP Server, visualisasi otomatis.

---

## Platform Configuration

Terhubung ke Impala CDW dengan environment variables berikut:

| Env Var | Value |
|---|---|
| `IMPALA_HOST` | `coordinator-default-impala-aws.dw-go01-demo-aws.ylcu-atmi.cloudera.site` |
| `IMPALA_PORT` | `443` |
| `IMPALA_HTTP_PATH` | `cliservice` |
| `CDP_USER` | CDP username |
| `CDP_PASS` | CDP password |
| `DB_NAME` | `cai_sdx_se_indonesia` |

**Tabel utama:** `cai_sdx_se_indonesia.customer_dormant_segment` — 10,000 rows, 47 columns (synthetic, non-PII)

---

## Repository Layout

```text
bank-jawa-timur/
├── ask-data/                        # Bank Jawa Timur — Customer Analytics PoC
│   ├── backend/                     # FastAPI + NL-to-SQL + ChromaDB RAG
│   │   ├── app/                     # Core app: main, services, schemas, db
│   │   ├── domain_config.yaml       # Domain customization: tabel, kolom, prompts
│   │   └── backend_entry.py         # CAI Application entry point
│   ├── frontend/                    # Next.js 15, Cloudera design system
│   │   └── frontend_entry.py        # CAI Application entry point
│   ├── mcp_server/                  # MCP Server — 6 structured analytics tools
│   │   ├── app/tools/               # sql_query, dormant_risk, campaign, rag_search
│   │   └── mcp_entry.py             # CAI Application entry point
│   ├── qwen_inference/              # Qwen2.5-14B-Instruct-AWQ vLLM inference server
│   │   ├── qwen_entry.py            # CAI Application entry point (GPU)
│   │   └── download_model.py        # Download model ke HF cache (jalankan di session)
│   ├── data/documents/              # PDF docs untuk RAG (tidak di-commit)
│   ├── chroma_db/                   # ChromaDB vector store (auto-generated, tidak di-commit)
│   ├── sql/                         # Impala DDL untuk customer_dormant_segment
│   ├── data_generation/             # Synthetic data generator (10,000 rows)
│   └── docs/                        # Deployment guide, project state, metadata
├── scripts/                         # Repo sync dan CAI helper scripts
└── README.md
```

---

## CAI Applications

Deploy dalam urutan: **Qwen → Backend → MCP → Frontend**

| Application | Entry Point | Resources |
|---|---|---|
| `bjt-ask-data-qwen` | `qwen_inference/qwen_entry.py` | GPU L40, vLLM |
| `bjt-ask-data-backend` | `backend/backend_entry.py` | 4 vCPU, 8 GB RAM |
| `bjt-ask-data-mcp` | `mcp_server/mcp_entry.py` | 2 vCPU, 4 GB RAM |
| `bjt-ask-data-frontend` | `frontend/frontend_entry.py` | 2 vCPU, 4 GB RAM |

---

## Fitur Utama

- NL-to-SQL via Qwen2.5-14B-Instruct-AWQ (vLLM) → Impala CDW
- RAG document Q&A via ChromaDB — auto-ingest PDF saat backend start, embedding `all-MiniLM-L6-v2`
- MCP Server: `sql_query`, `dormant_risk_summary`, `dormant_reason_breakdown`, `campaign_recommendation`, `campaign_summary_by_reason`, `rag_search`
- Visualisasi otomatis: bar, line, pie, table via Recharts
- Guardrails: PII blocking, SQL-only enforcement, bahasa jawaban mengikuti bahasa pertanyaan
- Session management via SQLite
- Domain customization via `domain_config.yaml` — ganti dataset tanpa ubah kode Python

---

## Pre-deployment Checklist

1. `python sync_project.py` — sync repo ke CAI session
2. `export HUGGING_FACE_HUB_TOKEN=hf_xxx` lalu `python data-intelligence/ask-data/qwen_inference/download_model.py` — download Qwen model (~8 GB)
3. Taruh PDF dokumen ke `ask-data/backend/data/documents/` — ChromaDB auto-ingest saat backend pertama start

---

## Referensi

| Resource | Deskripsi | Path |
|---|---|---|
| **CAI Deployment Guide** | Step-by-step deploy ke CAI — credential, env vars, verifikasi | [`ask-data/docs/CAI_DEPLOYMENT_GUIDE.md`](ask-data/docs/CAI_DEPLOYMENT_GUIDE.md) |
| **Project State** | Status implementasi, komponen done vs pending | [`ask-data/docs/project-state.md`](ask-data/docs/project-state.md) |
| **Schema & Data Dictionary** | 47 kolom `customer_dormant_segment`, tipe data, enum values | [`ask-data/docs/customer_dormant_segment_metadata.md`](ask-data/docs/customer_dormant_segment_metadata.md) |
| **Domain Customization** | Cara ganti dataset/domain tanpa ubah kode | [`ask-data/docs/CAI_DEPLOYMENT_GUIDE.md#ganti-domaindataset`](ask-data/docs/CAI_DEPLOYMENT_GUIDE.md) |
