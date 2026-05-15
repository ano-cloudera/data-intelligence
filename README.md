# Bank Jawa Timur — AI Analytics PoC

Cloudera AI demo workspace untuk Bank Jawa Timur.
AI-powered customer analytics assistant — NL-to-SQL, ChromaDB RAG, MCP Server, visualisasi otomatis.

Berisi empat application track, masing-masing deployable sebagai Cloudera AI Applications:

| Track | Description | Status |
|---|---|---|
| `ask-data` | Bank Jawa Timur — Customer Analytics PoC (NL-to-SQL + RAG) | Active |
| `fraud-ai-assistant` | Fraud detection assistant + ML workflows | Active |
| `healthcare` | Chest X-ray review assistant — YOLO + AWS Bedrock | Active |
| `agent-studio` | Experimental agents built on the Cloudera Agent SDK | Experimental |

---

## Shared Platform Configuration

All applications connect to the same Impala CDW and share these environment variables:

| Env Var | Value |
|---|---|
| `IMPALA_HOST` | `coordinator-default-impala-aws.dw-go01-demo-aws.ylcu-atmi.cloudera.site` |
| `IMPALA_PORT` | `443` |
| `IMPALA_HTTP_PATH` | `cliservice` |
| `CDP_USER` | CDP username |
| `CDP_PASS` | CDP password |
| `DB_NAME` | `cai_sdx_se_indonesia` |

**Core tables in `cai_sdx_se_indonesia`:**

- `customer_dormant_segment` — Bank Jatim PoC (10,000 rows, 47 columns, synthetic non-PII)
- `customers`, `deposits`, `credits`, `fraud_transactions` — shared generic tables

---

## Repository Layout

```text
bank-jawa-timur/
├── ask-data/                        # Bank Jawa Timur — Customer Analytics PoC
│   ├── backend/                     # FastAPI + NL-to-SQL + ChromaDB RAG
│   │   ├── app/                     # Core app: main, services, schemas, db
│   │   ├── llm/                     # Qwen SQL prompt + client
│   │   ├── schema/                  # customer_dormant_segment schema
│   │   └── backend_entry.py         # CAI Application entry point
│   ├── frontend/                    # Next.js 15, Cloudera design system
│   │   └── frontend_entry.py        # CAI Application entry point
│   ├── mcp_server/                  # MCP Server — 6 structured analytics tools
│   │   ├── app/tools/               # sql_query, dormant_risk, campaign, rag_search
│   │   └── mcp_entry.py             # CAI Application entry point
│   ├── qwen_inference/              # Qwen2.5-14B vLLM inference server
│   │   ├── qwen_entry.py            # CAI Application entry point (GPU)
│   │   └── download_model.py        # Script download model ke HF cache (jalankan di session)
│   ├── data/documents/              # 5 Bank Jatim PDF docs (RAG source, not committed)
│   ├── chroma_db/                   # ChromaDB vector store (not committed)
│   ├── scripts/                     # ingest_documents.py, local_bootstrap.sh
│   ├── sql/                         # Impala DDL for customer_dormant_segment
│   ├── data_generation/             # Synthetic data generator (10,000 rows)
│   └── docs/                        # project-state, deployment guide, metadata
├── fraud-ai-assistant/              # Fraud detection assistant + ML
│   ├── backend/
│   ├── frontend/
│   ├── ml-templates/
│   └── docs/
├── healthcare/                      # Healthcare demo — Xray Assist
│   └── Xray Assistant/
│       ├── backend/                 # FastAPI + YOLO inference + Bedrock GenAI
│       ├── frontend/                # Next.js, Cloudera design system
│       ├── docs/                    # Architecture, API, project state
│       └── references/             # Upstream YOLO + ChestX-Det references
├── agent-studio/                    # Agent SDK experiments
│   └── marketing-content-intelligence/
├── scripts/                         # Repo sync and CAI helper scripts
└── README.md
```

---

## Track Details

### `ask-data` — Bank Jawa Timur Customer Analytics PoC

AI-powered customer analytics assistant for Bank Jawa Timur. Business users ask questions
in Bahasa Indonesia about customer dormant risk, segmentation, campaign recommendations,
and deposit performance — no SQL required.

**4 CAI Applications (deploy order: Qwen → Backend → MCP → Frontend):**

| Application Name | Entry Point | Resources |
|---|---|---|
| `bjt-ask-data-qwen` | `qwen_inference/qwen_entry.py` | GPU L40, vLLM |
| `bjt-ask-data-backend` | `backend/backend_entry.py` | CPU 4 vCPU 8 GB |
| `bjt-ask-data-mcp` | `mcp_server/mcp_entry.py` | CPU 2 vCPU 4 GB |
| `bjt-ask-data-frontend` | `frontend/frontend_entry.py` | CPU 2 vCPU 4 GB |

**Key capabilities:**

- NL-to-SQL via Qwen2.5-14B-Instruct-AWQ (vLLM) → Impala CDW execution
- RAG document Q&A via ChromaDB (5 Bank Jatim PDFs, 17 chunks, `nomic-embed-text` embedding)
- MCP Server with 6 structured tools: `sql_query`, `dormant_risk_summary`, `dormant_reason_breakdown`, `campaign_recommendation`, `campaign_summary_by_reason`, `rag_search`
- Visualization spec generation (bar, line, pie, table) rendered via Recharts
- Local guardrails: PII blocking, SQL-only enforcement, Bahasa Indonesia output
- Session management via SQLite
- Next.js 15 frontend in Bahasa Indonesia — Cloudera-branded design system

**Data:** `cai_sdx_se_indonesia.customer_dormant_segment` — 10,000 rows, 47 columns (synthetic, non-PII)

**Pre-deployment checklist (jalankan di CAI Workbench session):**

1. `python sync_project.py` — sync repo ke session
2. `export HUGGING_FACE_HUB_TOKEN=hf_xxx` lalu `python bank-jawa-timur/ask-data/qwen_inference/download_model.py` — download Qwen model ke HF cache (~8 GB)
3. Upload atau ingest `chroma_db/` — pastikan `col.count()` = 17

See [`ask-data/docs/CAI_DEPLOYMENT_GUIDE.md`](ask-data/docs/CAI_DEPLOYMENT_GUIDE.md) for full step-by-step deployment instructions.
See [`ask-data/docs/project-state.md`](ask-data/docs/project-state.md) for implementation details.

---

### `fraud-ai-assistant`

Fraud-specific demo track combining an AI assistant with a full analytics console and ML workflows.

- FastAPI backend tuned for fraud analysis queries
- Next.js frontend with four core views: Dashboard, AI Assistant, Investigations, Model Management
- Fraud-aware schema and business context
- `ml-templates/` for baseline fraud model training and packaging
- Training workflow supports Impala as the primary CAI data source

See [`fraud-ai-assistant/docs/project-state.md`](fraud-ai-assistant/docs/project-state.md) for full implementation and deployment details.

---

### `healthcare` — Xray Assist

Healthcare-focused demo: chest X-ray upload, YOLO-based object detection, and GenAI-enriched clinical output.

- FastAPI backend with YOLO11 inference adapter and AWS Bedrock enrichment (Claude Sonnet)
- Next.js 15 frontend with Cloudera-branded design system — bilingual (EN / Bahasa Indonesia)
- GenAI output constrained to assistive, review-oriented language — never diagnostic
- Safe fallback: API never fails if Bedrock is unavailable
- Deployed as two separate Cloudera AI Applications (backend + frontend)

See [`healthcare/Xray Assistant/docs/project-state.md`](healthcare/Xray%20Assistant/docs/project-state.md) for full implementation and deployment details.

---

### `agent-studio`

Experimental track for agent applications built on the Cloudera Agent SDK.

- `marketing-content-intelligence/` — multi-agent pipeline for marketing content analysis

---

## Recommended Usage

### In Cloudera AI

- Keep GitHub as the source of truth
- Sync the CAI project from GitHub via `sync_project.py`
- Inject runtime configuration through CAI environment variables — never commit secrets
- Run backend and frontend as separate CAI Applications
- Use CAI Jobs for repeatable training, schema, or deployment tasks

### Locally

- Use the repo for editing, review, and documentation
- Use `sample/` CSV data for local fallback when Impala is not available
- Validate final runtime behavior in CAI — especially for networking and authentication

---

## Where To Start

| Track | Resource | Path |
|---|---|---|
| **ask-data** | CAI deployment guide | [`ask-data/docs/CAI_DEPLOYMENT_GUIDE.md`](ask-data/docs/CAI_DEPLOYMENT_GUIDE.md) |
| **ask-data** | Project state | [`ask-data/docs/project-state.md`](ask-data/docs/project-state.md) |
| **ask-data** | Schema & data dictionary | [`ask-data/docs/customer_dormant_segment_metadata.md`](ask-data/docs/customer_dormant_segment_metadata.md) |
| **ask-data** | App README | [`ask-data/README.md`](ask-data/README.md) |
| **fraud-ai-assistant** | Project state | [`fraud-ai-assistant/docs/project-state.md`](fraud-ai-assistant/docs/project-state.md) |
| **fraud-ai-assistant** | App README | [`fraud-ai-assistant/README.md`](fraud-ai-assistant/README.md) |
| **healthcare** | Project state | [`healthcare/Xray Assistant/docs/project-state.md`](healthcare/Xray%20Assistant/docs/project-state.md) |
| **agent-studio** | Folder | [`agent-studio/`](agent-studio/) |
