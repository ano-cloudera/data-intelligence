# CAI SE Indonesia Demo Workspace

This repository is the shared workspace for the CAI SE Indonesia demo environment on Cloudera AI.

It contains four application tracks:

- `ask-data` — general-purpose AI analytics assistant (Ask the Data / NL-to-SQL)
- `fraud-ai-assistant` — fraud-focused AI assistant with dashboard, investigations, and ML workflows
- `healthcare` — healthcare demo: chest X-ray review assistant powered by YOLO + AWS Bedrock
- `agent-studio` — experimental agent applications built with the Cloudera Agent SDK

## Current Shared Platform Configuration

These values are the current shared defaults for the CAI deployment:

- Impala database: `cai_sdx_se_indonesia`
- Shared data root: `s3a://go01-demo/user/cai-demo-se-indonesia/data/`
- Core tables:
  - `customers`
  - `deposits`
  - `credits`
  - `fraud_transactions`

Both `ask-data` and `fraud-ai-assistant` share the same Impala connection pattern via environment variables:

- `IMPALA_HOST`
- `IMPALA_PORT`
- `IMPALA_HTTP_PATH`
- `CDP_USER`
- `CDP_PASS`
- `DB_NAME`

## Repository Layout

```text
cai-se-indo-demo/
├── ask-data/                        # General analytics assistant
│   ├── backend/                     # FastAPI + NL-to-SQL
│   ├── frontend/                    # Next.js, Cloudera design system
│   └── docs/                        # API contract, setup, project state
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
├── sample/                          # Generated CSV data for local dev
├── scripts/                         # Repo sync and CAI helper scripts
├── generate_demo_data.py
├── impala_demo_ddl.sql
├── submit_impala_schema.py
└── README.md
```

## Main Components

### `ask-data`

General-purpose AI analytics assistant. Ask questions about structured data in natural language — no SQL knowledge required.

- FastAPI backend with NL-to-SQL via Azure OpenAI and Impala/CDW execution
- Next.js 15 frontend with Cloudera-branded design (dark navy sidebar, indigo accent, orange CTAs)
- Typography: Inter (body), Outfit (headings), JetBrains Mono (code/numeric) — all via Google Fonts
- Icons: `@mui/icons-material` throughout — no inline SVGs
- Read-only Impala query execution with SQL guardrails and PII blocking
- Generic enough to reuse across different banking or enterprise customers
- Deployed as two separate Cloudera AI Applications (backend + frontend)
- Optional RAG Studio integration for document-grounded answers, with per-session configuration stored in backend memory
- RAG answers surface source cards with an `Open Source PDF` action when source metadata is available
- Demo Guide redesigned for management-level audiences: Business Impact first, scannable bullets, ready-to-use demo prompts
- Usage Dashboard analytics glitch fixed — no more re-fetch loop on tab switch

See [`ask-data/docs/project-state.md`](ask-data/docs/project-state.md) for full implementation and deployment details.

### `fraud-ai-assistant`

Fraud-specific demo track combining an AI assistant with a full analytics console and ML workflows.

- FastAPI backend tuned for fraud analysis queries
- Next.js frontend with four core views: Dashboard, AI Assistant, Investigations, Model Management
- Fraud-aware schema and business context
- `ml-templates/` for baseline fraud model training and packaging
- Training workflow supports Impala as the primary CAI data source
- Deployed fraud model API validated in CAI

See [`fraud-ai-assistant/docs/project-state.md`](fraud-ai-assistant/docs/project-state.md) for full implementation and deployment details.

### `healthcare` — Xray Assist

Healthcare-focused demo: chest X-ray upload, YOLO-based object detection, and GenAI-enriched clinical output.

- FastAPI backend with YOLO11 inference adapter and AWS Bedrock enrichment (Claude Sonnet)
- Next.js 15 frontend with Cloudera-branded design — same design system as ask-data
- Typography: Inter (body), Outfit (headings), JetBrains Mono (numeric fields) — all via Google Fonts
- Icons: `@mui/icons-material` throughout — `MonitorHeartIcon`, `SummarizeIcon`, `BiotechIcon`, clinical notice icons
- Upload panel: unified control block (language, file picker, CTA) with orange gradient Analyze button
- Stat cards: dynamic color-coding by severity/confidence — rose/amber/green/blue based on result
- Topbar: single-line layout with icon + title + separator + subtitle
- Bilingual output: English / Bahasa Indonesia response language selection
- GenAI output constrained to assistive, review-oriented language — never diagnostic
- Safe fallback: API never fails if Bedrock is unavailable
- Deployed as two separate Cloudera AI Applications (backend + frontend)

See [`healthcare/Xray Assistant/docs/project-state.md`](healthcare/Xray%20Assistant/docs/project-state.md) for full implementation and deployment details.

### `agent-studio`

Experimental track for agent applications built on the Cloudera Agent SDK.

- `marketing-content-intelligence/` — multi-agent pipeline for marketing content analysis

### Shared files

- `sample/` — generated CSVs for local development and fallback testing
- `generate_demo_data.py` — produces synthetic demo datasets
- `impala_demo_ddl.sql` — shared Impala DDL for all core tables
- `submit_impala_schema.py` — applies the DDL to Impala from a configured Python session
- `scripts/` — repository sync and helper scripts used during CAI operations

## Recommended Usage Model

### In Cloudera AI

- keep GitHub as the source of truth
- sync the CAI project from GitHub
- inject runtime configuration through CAI environment variables (never commit secrets)
- run backend and frontend as separate CAI Applications
- use CAI Jobs for repeatable training, schema, or deployment tasks

### Locally

- use the repo for editing, review, and documentation
- use `sample/` CSV data for local fallback when Impala is not available
- validate final runtime behavior in CAI — especially for networking and authentication

## Where To Start

| Resource | Path |
|---|---|
| General analytics app | [`ask-data/README.md`](ask-data/README.md) |
| Ask-data project state | [`ask-data/docs/project-state.md`](ask-data/docs/project-state.md) |
| Fraud app | [`fraud-ai-assistant/README.md`](fraud-ai-assistant/README.md) |
| Fraud project state | [`fraud-ai-assistant/docs/project-state.md`](fraud-ai-assistant/docs/project-state.md) |
| Xray Assist (healthcare) | [`healthcare/Xray Assistant/docs/project-state.md`](healthcare/Xray%20Assistant/docs/project-state.md) |
| Agent studio | [`agent-studio/`](agent-studio/) |
