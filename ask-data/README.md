# Ask Data

`ask-data` is the general-purpose analytics assistant in this workspace.

It is designed for CAI demos where a user asks business questions in natural language and the application turns them into safe read-only SQL against Impala, executes the query, and returns a concise answer plus transparent SQL and preview data.

## Current Role In This Workspace

- reusable analytics assistant for banking and fraud-adjacent analysis
- secondary project in priority compared with `fraud-ai-assistant`
- shared consumer of the common Impala demo schema
- CAI-ready app split into backend and frontend applications

## Current Shared Data Configuration

The app is aligned to the current CAI demo configuration:

- Impala database: `cai_sdx_se_indonesia`
- shared data root: `s3a://go01-demo/user/cai-demo-se-indonesia/data/`
- expected tables:
  - `customers`
  - `deposits`
  - `credits`
  - `fraud_transactions`

## What The App Does

- accepts natural language business questions
- generates safe read-only SQL with table allowlisting
- executes SQL against Impala
- summarizes preview results in natural language
- preserves lightweight session context during a conversation
- supports both banking and fraud-adjacent demo questions

## Architecture

### Backend

The backend is a FastAPI service that handles:

- runtime configuration from CAI environment variables
- Impala connectivity
- Azure OpenAI-powered SQL generation
- SQL validation and execution guardrails
- answer generation grounded in query results
- in-memory session and conversation state

Primary backend guide:

- [`backend/README.md`](/Users/triano/Documents/Cloudera/cai-se-indo-demo/ask-data/backend/README.md)

### Frontend

The frontend is a Next.js application that handles:

- question input and session continuity
- backend and database health display
- answer-first result presentation
- generated SQL visibility
- query result preview rendering

Primary frontend guide:

- [`frontend/README.md`](/Users/triano/Documents/Cloudera/cai-se-indo-demo/ask-data/frontend/README.md)

## Folder Structure

```text
ask-data/
├── backend/
├── docs/
├── frontend/
└── README.md
```

## CAI Deployment Model

This project is intended to run in Cloudera AI as two separate Applications:

- backend application via `ask-data/backend/backend_entry.py`
- frontend application via `ask-data/frontend/frontend_entry.py`

Recommended runtime assumptions:

- configuration is injected through CAI environment variables
- frontend points to the backend with `NEXT_PUBLIC_API_BASE_URL`
- the backend uses `DB_NAME=cai_sdx_se_indonesia`
- both apps are synced from GitHub and validated in CAI

## Typical Questions It Should Support

- customer balance and product mix questions
- deposit and credit summaries
- trend analysis by date or branch
- high-level fraud rate or suspicious activity exploration
- fraud distribution by channel, city, device, or segment

## Key Documentation

- project status and handoff: [`docs/project-state.md`](/Users/triano/Documents/Cloudera/cai-se-indo-demo/ask-data/docs/project-state.md)
- environment variables: [`docs/env.md`](/Users/triano/Documents/Cloudera/cai-se-indo-demo/ask-data/docs/env.md)
- setup guidance: [`docs/setup.md`](/Users/triano/Documents/Cloudera/cai-se-indo-demo/ask-data/docs/setup.md)

---

## Bank Jawa Timur PoC — Local Qwen + Impala Iceberg

### PoC Objective

AI chatbot (Ask Data) untuk Bank Jawa Timur. Pengguna mengajukan pertanyaan analitik perbankan dalam Bahasa Indonesia. Backend men-generate SQL dari natural language, mengeksekusi ke Impala Iceberg, dan merangkum hasil dalam Bahasa Indonesia.

### Main Table

```
cai_sdx_se_indonesia.customer_dormant_segment
```

Use cases: segmentasi nasabah, klasifikasi dormant, rekomendasi campaign, analitik cabang/segmen/channel.

### Start Local Qwen (vLLM)

```bash
cd ask-data
bash scripts/local_bootstrap.sh

export QWEN_MODEL="Qwen/Qwen3-8B-AWQ"
export QWEN_MAX_MODEL_LEN=4096
export QWEN_GPU_MEMORY_UTILIZATION=0.85

bash qwen_inference/start_qwen_vllm.sh
bash qwen_inference/test_qwen.sh
```

### Backend Env Vars

```bash
LLM_PROVIDER=local_qwen
QWEN_BASE_URL=http://localhost:8000/v1
QWEN_API_KEY=local-dev-token
QWEN_MODEL=Qwen/Qwen3-8B-AWQ
DB_NAME=cai_sdx_se_indonesia
SQL_ALLOWED_TABLES=customer_dormant_segment
```

### Generate Sample Data

```bash
cd ask-data
python data_generation/generate_customer_dormant_segment_data.py --rows 10000 --output-dir data
# Output: data/customer_dormant_segment.csv
```

### Create Impala Iceberg Table

```bash
# View DDL:
cat sql/impala_customer_dormant_segment_ddl.sql
# Run in Impala or via Hue:
# CREATE TABLE cai_sdx_se_indonesia.customer_dormant_segment ... STORED BY ICEBERG;
```

### Makefile Shortcuts

```bash
make bootstrap    # install qwen inference deps
make qwen         # start vLLM server
make test-qwen    # test Qwen inference
make sample-data  # generate 10k rows CSV
make ddl          # print Impala DDL
```

### PII / Guardrails

Requests for NIK, KTP, CIF, nomor rekening, nomor HP, email, atau alamat diblokir otomatis. customer_id hanya digunakan sebagai identifier analitik sintetis.

### Cloudera AI ECS Deployment

- Backend: Cloudera AI Application (Python, uvicorn)
- Frontend: Cloudera AI Application (Node.js, Next.js)
- Qwen/vLLM: Cloudera AI Workbench session dengan GPU, atau CAI Application terpisah
- Impala: Cloudera Data Warehouse (Iceberg)
- Set `QWEN_BASE_URL` ke URL aplikasi Qwen jika di-deploy sebagai CAI Application
